"""
키워드 점수화 & 랭킹 서비스
keyword_candidates + whereispost 데이터를 결합하여 최종 점수를 계산합니다.
"""
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.config import SCORING_WEIGHTS
from app.models.keyword_candidate import KeywordCandidate
from app.models.keyword_ranking import KeywordRanking
from app.models.weekly_run import WeeklyRun
from app.services.whereispost import fetch_keyword_metrics
from app.utils.logger import get_logger

logger = get_logger("keyword_scorer")


async def score_and_rank_keywords(
    db: AsyncSession,
    week_key: str,
    weights: dict | None = None,
) -> list[KeywordRanking]:
    """Score keyword candidates and create rankings."""

    w = weights or SCORING_WEIGHTS

    # Fetch candidates
    result = await db.execute(
        select(KeywordCandidate).where(KeywordCandidate.week_key == week_key)
    )
    candidates = result.scalars().all()

    if not candidates:
        logger.warning(f"No keyword candidates for {week_key}")
        return []

    # Clear existing rankings for this week (rerank scenario)
    await db.execute(
        delete(KeywordRanking).where(KeywordRanking.week_key == week_key)
    )

    # Fetch all source items for this week for advanced metrics
    from app.models.source_item import SourceItem
    result_sources = await db.execute(select(SourceItem).where(SourceItem.week_key == week_key))
    all_sources = result_sources.scalars().all()
    source_dict = {s.id: s for s in all_sources}

    rankings = []

    for cand in candidates:
        # Fetch metrics from whereispost
        try:
            metrics = await fetch_keyword_metrics(cand.keyword)
        except Exception as e:
            logger.warning(f"Metrics fetch failed for '{cand.keyword}': {e}")
            metrics = {"search_volume": 0, "document_count": 0, "keyword_ratio": 0.0}

        search_volume = metrics["search_volume"]
        document_count = metrics["document_count"]
        keyword_ratio = metrics["keyword_ratio"]

        # Calculate advanced metrics
        cand_sources = [source_dict[sid] for sid in (cand.source_item_ids_json or []) if sid in source_dict]
        
        # 1. Title inclusion
        title_inclusion_count = sum(1 for s in cand_sources if cand.keyword.lower() in s.title.lower())
        
        # 2. Multi source (Naver + Yahoo)
        sites = {s.source_site for s in cand_sources}
        is_multi_source = len(sites) > 1

        # Calculate scores
        # Base: news count * 3 + symbol count * 5
        # Title inclusion: +3 per title
        # Multi source: +5 bonus
        issue_score = (
            cand.related_news_count * w.get("news_factor", 3)
            + cand.related_symbol_count * w.get("symbol_factor", 5)
            + title_inclusion_count * 3
            + (5 if is_multi_source else 0)
        )

        search_score = math.log10(search_volume + 1) * 10
        competition_penalty = math.log10(document_count + 1) * 3

        final_score = (
            issue_score * w.get("issue", 1.0)
            + search_score * w.get("search", 1.5)
            - competition_penalty * w.get("competition", 0.8)
        )

        # Competition level
        if document_count < 50000:
            competition_level = "low"
        elif document_count < 200000:
            competition_level = "medium"
        else:
            competition_level = "high"

        # Recommended channel
        if competition_level == "low" and search_volume > 500:
            recommended_channel = "naver"
        elif competition_level == "high":
            recommended_channel = "tistory"
        else:
            recommended_channel = "both"

        extra_metrics = {
            "title_inclusion_count": title_inclusion_count,
            "is_multi_source": is_multi_source,
            "source_sites": list(sites)
        }

        ranking = KeywordRanking(
            week_key=week_key,
            keyword=cand.keyword,
            keyword_type=cand.keyword_type,
            recommendation_reasons_json=cand.recommendation_reasons_json,
            final_score=round(final_score, 2),
            issue_score=round(issue_score, 2),
            search_score=round(search_score, 2),
            competition_penalty=round(competition_penalty, 2),
            search_volume=search_volume,
            document_count=document_count,
            keyword_ratio=keyword_ratio,
            related_news_count=cand.related_news_count,
            related_symbol_count=cand.related_symbol_count,
            summary_line=cand.origin_summary,
            competition_level=competition_level,
            recommended_channel=recommended_channel,
            is_doc_count_100k_plus=document_count >= 100000,
            extra_metrics_json=extra_metrics
        )
        rankings.append(ranking)

    # Sort by final_score desc and assign rank
    rankings.sort(key=lambda r: float(r.final_score or 0), reverse=True)
    for i, r in enumerate(rankings):
        r.rank_no = i + 1
        db.add(r)

    # Update weekly run keyword count
    run_result = await db.execute(
        select(WeeklyRun)
        .where(WeeklyRun.week_key == week_key)
        .order_by(WeeklyRun.created_at.desc())
    )
    run = run_result.scalars().first()
    if run:
        run.total_keyword_count = len(rankings)

    await db.commit()
    logger.info(f"Ranked {len(rankings)} keywords for {week_key}")
    return rankings
