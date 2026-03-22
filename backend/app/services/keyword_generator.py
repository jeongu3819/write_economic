"""
키워드 후보 생성 서비스
수집된 source_items를 OpenAI API로 분석하여 키워드 후보를 추출합니다.
"""
import json
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.source_item import SourceItem
from app.models.keyword_candidate import KeywordCandidate
from app.utils.logger import get_logger

logger = get_logger("keyword_generator")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

KEYWORD_EXTRACTION_PROMPT = """다음 뉴스/이슈 목록을 분석하여 네이버/Tistory 블로그 작성에 매우 적합한 맞춤형 추천 키워드를 추출해주세요.

## 추출 기준 및 규칙
1. 15~25개의 키워드 후보를 추출합니다.
2. 각 키워드의 성격(keyword_type)을 다음 3가지 중 하나로 명확하게 분류하세요:
   - "traffic": 조회수/대중 관심 유도용 숏 텀 이슈 (예: 트럼프 관세, AI 반도체, 유가 급등)
   - "investment": 실제 주식/투자자 관심형 (예: 실적 발표, 가이던스 상향, 공매도 리포트)
   - "blog_title": 블로그 제목에 바로 넣기 좋은 구/절 형태 (예: '트럼프 관세 수혜주 정리', '테슬라 생산량 감소 원인')
3. 불용어(의미가 약한 단어: 오늘, 관련, 발표, 뉴스, 기사, 가능성, 전망 등) 단독 키워드 추출을 엄격히 금지합니다.
4. 기업명, 산업 키워드, 한글/영문 혼합(예: AI, 테슬라, BYD)을 살리되 유사한 내용은 하나로 통합하세요.
5. ★중요★ 해외(Yahoo)와 국내(Naver) 얼론 양쪽에서 공통으로 다루는 내용, 여러 기사에서 반복 등장하는 내용을 최우선 핵심 키워드로 뽑으세요.
6. 이 키워드를 추천하는 명확한 근거(reasons)를 배열로 2~3개 작성해주세요.
   - 예: ["최근 24시간 동안 관련 뉴스 5건 집중", "Naver와 Yahoo 뉴스 양쪽에 공통 등장", "투자자 검색 유입 가능성이 매우 높음"]
7. 각 키워드에 대해 관련 뉴스 수, 관련 종목 수, 1줄 요약도 함께 제공합니다.
8. 반드시 한국어로 작성합니다.

## 출력 형식 (JSON 배열)
각 항목은 아래 형태를 따르세요:
{
  "keyword": "키워드명",
  "keyword_type": "traffic|investment|blog_title",
  "origin_summary": "1줄 요약 (국내외 공통 이슈 강조)",
  "reasons": ["추천 근거 1", "추천 근거 2"],
  "related_news_count": 숫자,
  "related_symbol_count": 숫자,
  "source_ids": [사용된 뉴스 인덱스 번호 리스트]
}
"""

KEYWORD_SCHEMA = {
    "type": "object",
    "properties": {
        "keywords": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "keyword_type": {"type": "string", "enum": ["traffic", "investment", "blog_title"]},
                    "origin_summary": {"type": "string"},
                    "reasons": {"type": "array", "items": {"type": "string"}},
                    "related_news_count": {"type": "integer"},
                    "related_symbol_count": {"type": "integer"},
                    "source_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["keyword", "keyword_type", "origin_summary", "reasons", "related_news_count", "related_symbol_count", "source_ids"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["keywords"],
    "additionalProperties": False,
}


async def generate_keywords(db: AsyncSession, week_key: str) -> list[KeywordCandidate]:
    """Generate keyword candidates from collected source items."""

    # Fetch source items for this week
    result = await db.execute(
        select(SourceItem).where(SourceItem.week_key == week_key)
    )
    sources = result.scalars().all()

    if not sources:
        logger.warning(f"No source items found for {week_key}")
        return []

    # Build source text for OpenAI
    source_lines = []
    for i, src in enumerate(sources):
        source_lines.append(f"[{i}] [{src.source_site}] {src.title} — {src.summary or ''}")

    source_text = "\n".join(source_lines)

    # Call OpenAI
    try:
        response = await client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": KEYWORD_EXTRACTION_PROMPT},
                {"role": "user", "content": f"이번 주({week_key}) 수집된 뉴스/이슈:\n\n{source_text}"},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "keyword_candidates",
                    "schema": KEYWORD_SCHEMA,
                    "strict": True,
                }
            },
        )

        output_text = response.output_text
        data = json.loads(output_text)
        keyword_list = data.get("keywords", [])

    except Exception as e:
        logger.error(f"OpenAI keyword generation failed: {e}")
        raise

    # Save to DB
    candidates = []
    for kw in keyword_list:
        source_ids = kw.get("source_ids", [])
        real_ids = []
        for idx in source_ids:
            if 0 <= idx < len(sources):
                real_ids.append(sources[idx].id)

        candidate = KeywordCandidate(
            week_key=week_key,
            keyword=kw["keyword"],
            keyword_type=kw.get("keyword_type", "traffic"),
            recommendation_reasons_json=kw.get("reasons", []),
            origin_summary=kw.get("origin_summary", ""),
            related_news_count=kw.get("related_news_count", 0),
            related_symbol_count=kw.get("related_symbol_count", 0),
            source_item_ids_json=real_ids,
        )
        db.add(candidate)
        candidates.append(candidate)

    await db.commit()
    logger.info(f"Generated {len(candidates)} keyword candidates for {week_key}")
    return candidates
