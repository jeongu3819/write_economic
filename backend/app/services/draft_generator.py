"""
블로그 초안 생성 서비스
분석 프롬프트 → 네이버형/티스토리형 프롬프트 2단계로 생성합니다.
"""
import json
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.keyword_ranking import KeywordRanking
from app.models.source_item import SourceItem
from app.models.blog_draft import BlogDraft
from app.prompts.analysis import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_SCHEMA
from app.prompts.naver_blog import NAVER_BLOG_SYSTEM_PROMPT, NAVER_BLOG_SCHEMA
from app.prompts.tistory_blog import TISTORY_BLOG_SYSTEM_PROMPT, TISTORY_BLOG_SCHEMA
from app.utils.logger import get_logger

logger = get_logger("draft_generator")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def generate_draft(db: AsyncSession, keyword_ranking_id: int) -> BlogDraft:
    """Generate a blog draft for the given keyword ranking."""

    # Fetch keyword ranking
    result = await db.execute(
        select(KeywordRanking).where(KeywordRanking.id == keyword_ranking_id)
    )
    ranking = result.scalars().first()
    if not ranking:
        raise ValueError(f"KeywordRanking {keyword_ranking_id} not found")

    # Fetch related source items
    source_result = await db.execute(
        select(SourceItem).where(SourceItem.week_key == ranking.week_key)
    )
    sources = source_result.scalars().all()

    source_text = "\n".join(
        [f"- [{s.source_site}] {s.title}: {s.summary or ''}" for s in sources[:20]]
    )

    # --- Step 1: Analysis ---
    logger.info(f"Generating analysis for '{ranking.keyword}'...")
    analysis_data = await _call_openai(
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        user_prompt=f"키워드: {ranking.keyword}\n이슈 요약: {ranking.summary_line}\n\n관련 뉴스/이슈:\n{source_text}",
        schema=ANALYSIS_SCHEMA,
        schema_name="analysis_result",
    )

    analysis_json_str = json.dumps(analysis_data, ensure_ascii=False)

    # --- Step 2: Naver Blog ---
    logger.info(f"Generating Naver blog draft for '{ranking.keyword}'...")
    naver_data = await _call_openai(
        system_prompt=NAVER_BLOG_SYSTEM_PROMPT,
        user_prompt=f"아래 분석 자료를 바탕으로 네이버 블로그 글을 작성해주세요:\n\n{analysis_json_str}",
        schema=NAVER_BLOG_SCHEMA,
        schema_name="naver_blog_result",
    )

    # --- Step 3: Tistory Blog ---
    logger.info(f"Generating Tistory blog draft for '{ranking.keyword}'...")
    tistory_data = await _call_openai(
        system_prompt=TISTORY_BLOG_SYSTEM_PROMPT,
        user_prompt=f"아래 분석 자료를 바탕으로 티스토리 블로그 글을 작성해주세요:\n\n{analysis_json_str}",
        schema=TISTORY_BLOG_SCHEMA,
        schema_name="tistory_blog_result",
    )

    # --- Save Draft ---
    draft = BlogDraft(
        week_key=ranking.week_key,
        keyword_ranking_id=ranking.id,
        keyword=ranking.keyword,
        title_candidates_json=naver_data.get("title_candidates", []),
        intro_candidates_json=naver_data.get("intro_candidates", []),
        body_naver=naver_data.get("body", ""),
        body_tistory_md=tistory_data.get("body_markdown", ""),
        body_tistory_html=tistory_data.get("body_html", ""),
        summary_text=analysis_data.get("source_summary", ""),
        hashtags_json=list(set(
            naver_data.get("hashtags", []) + tistory_data.get("hashtags", [])
        )),
        caution_note=naver_data.get("caution_note", ""),
        status="draft",
    )
    db.add(draft)
    await db.commit()
    await db.refresh(draft)

    logger.info(f"Draft #{draft.id} created for '{ranking.keyword}'")
    return draft


async def _call_openai(
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    schema_name: str,
) -> dict:
    """Call OpenAI Responses API with structured output."""
    try:
        response = await client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        return json.loads(response.output_text)
    except Exception as e:
        logger.error(f"OpenAI call failed ({schema_name}): {e}")
        raise
