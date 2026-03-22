"""Issues/Collection router."""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.weekly_run import WeeklyRun
from app.models.source_item import SourceItem
from app.models.keyword_ranking import KeywordRanking
from app.schemas.issues import CollectRequest, WeeklyRunOut, SourceItemOut
from app.schemas.keywords import KeywordRankingOut
from app.services.collector import collect_issues
from app.services.keyword_generator import generate_keywords
from app.services.keyword_scorer import score_and_rank_keywords
from app.utils.response import api_response
from app.utils.week import get_current_week_key, get_week_display

router = APIRouter(prefix="/api/issues", tags=["issues"])


async def _full_pipeline(week_key: str):
    """Background task: collect → generate keywords → score & rank."""
    from app.database import async_session
    async with async_session() as db:
        try:
            await collect_issues(db, week_key)
            await generate_keywords(db, week_key)
            await score_and_rank_keywords(db, week_key)
        except Exception as e:
            import traceback
            traceback.print_exc()


@router.post("/collect-weekly")
async def collect_weekly(
    body: CollectRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start weekly issue collection pipeline (월요일~일요일 기준)."""
    week_key = body.week_key or get_current_week_key()

    # Check if already running
    result = await db.execute(
        select(WeeklyRun)
        .where(WeeklyRun.week_key == week_key, WeeklyRun.status == "running")
    )
    existing = result.scalars().first()
    if existing:
        return api_response(
            data={
                "week_key": week_key,
                "status": "already_running",
                "display": get_week_display(week_key),
            },
        )

    # Run full pipeline in background
    background_tasks.add_task(_full_pipeline, week_key)

    return api_response(
        data={
            "week_key": week_key,
            "status": "started",
            "display": get_week_display(week_key),
        },
    )


# 하위 호환: 기존 /collect 엔드포인트 유지
@router.post("/collect")
async def collect(
    body: CollectRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Legacy endpoint — redirects to collect-weekly."""
    return await collect_weekly(body, background_tasks, db)


@router.get("/weeks")
async def list_weeks(db: AsyncSession = Depends(get_db)):
    """List all weeks with runs."""
    result = await db.execute(
        select(WeeklyRun).order_by(WeeklyRun.created_at.desc())
    )
    runs = result.scalars().all()
    data = []
    for r in runs:
        d = WeeklyRunOut.model_validate(r).model_dump()
        d["display"] = get_week_display(r.week_key)
        data.append(d)
    return api_response(data=data)


@router.get("/{week_key}/sources")
async def get_sources(week_key: str, db: AsyncSession = Depends(get_db)):
    """Get source items for a specific week."""
    result = await db.execute(
        select(SourceItem).where(SourceItem.week_key == week_key)
    )
    items = result.scalars().all()
    return api_response(
        data=[SourceItemOut.model_validate(i).model_dump() for i in items]
    )


@router.get("/{week_key}/status")
async def get_week_status(week_key: str, db: AsyncSession = Depends(get_db)):
    """Get the status of a weekly run."""
    result = await db.execute(
        select(WeeklyRun)
        .where(WeeklyRun.week_key == week_key)
        .order_by(WeeklyRun.created_at.desc())
    )
    run = result.scalars().first()
    if not run:
        return api_response(data={"status": "not_found"})
    d = WeeklyRunOut.model_validate(run).model_dump()
    d["display"] = get_week_display(week_key)
    return api_response(data=d)


@router.get("/{week_key}/top-keywords")
async def get_top_keywords(week_key: str, db: AsyncSession = Depends(get_db)):
    """Get top 10 keywords for a week (convenience endpoint)."""
    result = await db.execute(
        select(KeywordRanking)
        .where(KeywordRanking.week_key == week_key)
        .order_by(KeywordRanking.rank_no)
        .limit(10)
    )
    rankings = result.scalars().all()
    return api_response(
        data=[KeywordRankingOut.model_validate(r).model_dump() for r in rankings]
    )


@router.delete("/runs/{week_key}")
async def delete_weekly_run(week_key: str, db: AsyncSession = Depends(get_db)):
    """Delete a weekly run and all its associated data."""
    from app.models.blog_draft import BlogDraft
    from app.models.keyword_candidate import KeywordCandidate
    from sqlalchemy import delete

    # Delete drafted blogs
    await db.execute(delete(BlogDraft).where(BlogDraft.week_key == week_key))
    # Delete rankings
    await db.execute(delete(KeywordRanking).where(KeywordRanking.week_key == week_key))
    # Delete candidates
    await db.execute(delete(KeywordCandidate).where(KeywordCandidate.week_key == week_key))
    # Delete sources
    await db.execute(delete(SourceItem).where(SourceItem.week_key == week_key))
    # Delete run
    await db.execute(delete(WeeklyRun).where(WeeklyRun.week_key == week_key))
    
    await db.commit()
    return api_response(data={"deleted": True})
