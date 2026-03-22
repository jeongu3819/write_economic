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

KEYWORD_EXTRACTION_PROMPT = """다음 뉴스/이슈 목록을 분석하여 블로그 작성에 적합한 키워드 후보를 추출해주세요.

## 규칙
1. 15~25개의 키워드 후보를 추출합니다.
2. 각 키워드는 블로그 주제로 적합해야 합니다.
3. 유사한 키워드는 하나로 통합합니다. (예: "삼성전자 실적" vs "삼성전자 분기실적" → 하나로)
4. 각 키워드에 대해 관련 뉴스 수, 관련 종목 수, 1줄 요약을 제공합니다.
5. 반드시 한국어로 작성합니다.

## 출력 형식 (JSON 배열)
각 항목은 아래 형태입니다:
{
  "keyword": "키워드명",
  "origin_summary": "이 키워드가 왜 이슈인지 1줄 요약",
  "related_news_count": 숫자,
  "related_symbol_count": 숫자,
  "source_ids": [관련 뉴스 인덱스 번호들]
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
                    "origin_summary": {"type": "string"},
                    "related_news_count": {"type": "integer"},
                    "related_symbol_count": {"type": "integer"},
                    "source_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["keyword", "origin_summary", "related_news_count", "related_symbol_count"],
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
