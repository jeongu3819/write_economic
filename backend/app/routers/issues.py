"""Issues/Collection router."""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.weekly_run import WeeklyRun
from app.models.source_item import SourceItem
from app.schemas.issues import CollectRequest, WeeklyRunOut, SourceItemOut
from app.services.collector import collect_issues
from app.services.keyword_generator import generate_keywords
from app.services.keyword_scorer import score_and_rank_keywords
from app.utils.response import api_response
from app.utils.week import get_current_week_key

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


@router.post("/collect")
async def collect(
    body: CollectRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start issue collection pipeline."""
    week_key = body.week_key or get_current_week_key()

    # Check if already running
    result = await db.execute(
        select(WeeklyRun)
        .where(WeeklyRun.week_key == week_key, WeeklyRun.status == "running")
    )
    existing = result.scalars().first()
    if existing:
        return api_response(
            data={"week_key": week_key, "status": "already_running"},
        )

    # Run full pipeline in background
    background_tasks.add_task(_full_pipeline, week_key)

    return api_response(
        data={"week_key": week_key, "status": "started"},
    )


@router.get("/weeks")
async def list_weeks(db: AsyncSession = Depends(get_db)):
    """List all weeks with runs."""
    result = await db.execute(
        select(WeeklyRun).order_by(WeeklyRun.created_at.desc())
    )
    runs = result.scalars().all()
    return api_response(
        data=[WeeklyRunOut.model_validate(r).model_dump() for r in runs]
    )


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
    return api_response(
        data=WeeklyRunOut.model_validate(run).model_dump()
    )
