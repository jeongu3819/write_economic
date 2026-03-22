"""Keywords router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.keyword_ranking import KeywordRanking
from app.schemas.keywords import KeywordGenerateRequest, RerankRequest, KeywordRankingOut
from app.services.keyword_generator import generate_keywords
from app.services.keyword_scorer import score_and_rank_keywords
from app.utils.response import api_response

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.post("/generate")
async def generate(body: KeywordGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate keyword candidates from collected sources."""
    candidates = await generate_keywords(db, body.week_key)
    return api_response(data={"count": len(candidates), "week_key": body.week_key})


@router.get("/{week_key}")
async def get_keywords(week_key: str, db: AsyncSession = Depends(get_db)):
    """Get all keyword rankings for a week."""
    result = await db.execute(
        select(KeywordRanking)
        .where(KeywordRanking.week_key == week_key)
        .order_by(KeywordRanking.rank_no)
    )
    rankings = result.scalars().all()
    return api_response(
        data=[KeywordRankingOut.model_validate(r).model_dump() for r in rankings]
    )


@router.get("/{week_key}/top")
async def get_top_keywords(
    week_key: str,
    min_doc_count: int = Query(default=0, description="Minimum document count filter"),
    limit: int = Query(default=10),
    db: AsyncSession = Depends(get_db),
):
    """Get top N keyword rankings for a week."""
    query = (
        select(KeywordRanking)
        .where(KeywordRanking.week_key == week_key)
    )
    if min_doc_count > 0:
        query = query.where(KeywordRanking.document_count >= min_doc_count)

    query = query.order_by(KeywordRanking.rank_no).limit(limit)
    result = await db.execute(query)
    rankings = result.scalars().all()
    return api_response(
        data=[KeywordRankingOut.model_validate(r).model_dump() for r in rankings]
    )


@router.post("/{week_key}/rerank")
async def rerank(week_key: str, body: RerankRequest, db: AsyncSession = Depends(get_db)):
    """Re-rank keywords with custom weights."""
    weights = {
        "issue": body.weight_issue,
        "search": body.weight_search,
        "competition": body.weight_competition,
        "news_factor": 3,
        "symbol_factor": 5,
        "filing_factor": 2,
    }
    rankings = await score_and_rank_keywords(db, week_key, weights)
    return api_response(
        data=[KeywordRankingOut.model_validate(r).model_dump() for r in rankings[:10]]
    )
