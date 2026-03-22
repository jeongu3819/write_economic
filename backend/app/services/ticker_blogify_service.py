"""
티커 분석 결과 → 블로그 변환 서비스
네이버 블로그형 기본 / 티스토리형 확장 가능 구조.
"""
import json
from openai import AsyncOpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.utils.logger import get_logger

logger = get_logger("ticker_blogify")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

BLOGIFY_PROMPT = """당신은 금융 전문 블로그 작가입니다.
아래 제공되는 종목 분석 데이터를 바탕으로 네이버 블로그에 적합한 글을 생성해주세요.

## 규칙
1. 제목은 호기심을 자극하는 형태로 3개 생성
2. 도입부는 독자의 관심을 유도하는 2~3문장으로 2개 생성
3. 본문은 자연스러운 블로그 톤으로 작성 (이모지 적절히 활용)
4. 핵심 요약은 3~5줄로 간결하게
5. 해시태그는 5~8개
6. 주의문구는 투자 면책 조항 포함
7. 한국어로 작성
8. 이미지 및 주가 그래프 언급 금지

## 출력 형식 (JSON)
{
  "titles": ["제목1", "제목2", "제목3"],
  "intros": ["도입부1", "도입부2"],
  "body": "본문 (마크다운)",
  "summary": "핵심 요약",
  "hashtags": ["태그1", "태그2", ...],
  "caution": "주의문구",
  "platform": "naver"
}
"""

BLOGIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "titles": {"type": "array", "items": {"type": "string"}},
        "intros": {"type": "array", "items": {"type": "string"}},
        "body": {"type": "string"},
        "summary": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "caution": {"type": "string"},
        "platform": {"type": "string"},
    },
    "required": ["titles", "intros", "body", "summary", "hashtags", "caution", "platform"],
    "additionalProperties": False,
}


async def blogify_ticker(analysis_data: dict, platform: str = "naver", model: str | None = None) -> dict:
    """
    티커 분석 결과를 블로그 형식으로 변환.
    
    Args:
        analysis_data: ticker_service.analyze_ticker()의 반환 결과
        platform: "naver" 또는 "tistory"
        model: 사용할 OpenAI 모델
    
    Returns:
        블로그 변환 결과 딕셔너리
    """
    use_model = model or OPENAI_MODEL
    ticker = analysis_data.get("ticker", "")

    # 분석 데이터 요약 텍스트
    news_text = "\n".join(
        [f"- [{n.get('type', '뉴스')}] {n['title']}" +
         (f" ({n.get('relative_time', '')})" if n.get('relative_time') else "") +
         (f": {n['summary']}" if n.get('summary') else "")
         for n in analysis_data.get("news", [])]
    ) or "뉴스 없음"

    filing_text = "\n".join(
        [f"- [{f.get('type', '공시')}] {f['title']}" +
         (f" ({f.get('relative_time', '')})" if f.get('relative_time') else "") +
         (f": {f['summary']}" if f.get('summary') else "")
         for f in analysis_data.get("filings", [])]
    ) or "공시 없음"

    user_prompt = f"""종목: {ticker}
기업개요: {analysis_data.get('company_overview', '정보 없음')[:400]}

최신 뉴스:
{news_text}

최신 공시:
{filing_text}

공매도 비율: {analysis_data.get('short_interest', '데이터 없음')}

트레이더 판단: {analysis_data.get('trader_sentiment', '중립')}
트레이더 해석: {analysis_data.get('trader_interpretation', '')}

플랫폼: {platform}
위 정보를 바탕으로 {platform} 블로그에 적합한 글을 작성해주세요."""

    try:
        response = await client.responses.create(
            model=use_model,
            input=[
                {"role": "system", "content": BLOGIFY_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "blog_result",
                    "schema": BLOGIFY_SCHEMA,
                    "strict": True,
                }
            },
        )

        result = json.loads(response.output_text)
        result["ticker"] = ticker
        result["platform"] = platform
        return result

    except Exception as e:
        logger.error(f"Blogify failed for {ticker}: {e}")
        # 기본 결과 반환
        return {
            "ticker": ticker,
            "titles": [f"{ticker} 분석: 최신 뉴스와 공시 정리"],
            "intros": [f"오늘 {ticker} 종목의 주요 이슈를 정리했습니다."],
            "body": f"# {ticker} 분석\n\n블로그 본문 생성에 실패했습니다. 직접 작성해주세요.",
            "summary": "AI 요약 생성 실패",
            "hashtags": [ticker, "주식", "투자", "분석"],
            "caution": "⚠️ 본 분석은 정보 제공 목적이며 투자 권유가 아닙니다.",
            "platform": platform,
        }
