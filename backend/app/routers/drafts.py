"""Drafts router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.blog_draft import BlogDraft
from app.schemas.drafts import DraftGenerateRequest, BlogDraftOut
from app.services.draft_generator import generate_draft
from app.utils.response import api_response

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


@router.post("/generate")
async def create_draft(body: DraftGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate a new blog draft for a keyword ranking."""
    draft = await generate_draft(db, body.keyword_ranking_id, body.model)
    return api_response(
        data=BlogDraftOut.model_validate(draft).model_dump()
    )


@router.get("/by-ranking/{ranking_id}")
async def get_draft_by_ranking(ranking_id: int, db: AsyncSession = Depends(get_db)):
    """Get a draft by its keyword ranking id."""
    result = await db.execute(
        select(BlogDraft)
        .where(BlogDraft.keyword_ranking_id == ranking_id, BlogDraft.status == "draft")
        .order_by(BlogDraft.created_at.desc())
    )
    draft = result.scalars().first()
    if not draft:
        return api_response(data=None)
    return api_response(data=BlogDraftOut.model_validate(draft).model_dump())




@router.get("")
async def list_drafts(
    week_key: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """List drafts, optionally filtered by week."""
    query = select(BlogDraft).order_by(BlogDraft.created_at.desc())
    if week_key:
        query = query.where(BlogDraft.week_key == week_key)

    result = await db.execute(query)
    drafts = result.scalars().all()
    return api_response(
        data=[BlogDraftOut.model_validate(d).model_dump() for d in drafts]
    )


@router.get("/{draft_id}")
async def get_draft(draft_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific draft."""
    result = await db.execute(
        select(BlogDraft).where(BlogDraft.id == draft_id)
    )
    draft = result.scalars().first()
    if not draft:
        return api_response(success=False, error="Draft not found")
    return api_response(
        data=BlogDraftOut.model_validate(draft).model_dump()
    )


@router.post("/{draft_id}/regenerate")
async def regenerate_draft(
    draft_id: int, 
    model: str = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate a draft (creates a new version) with a selected model."""
    result = await db.execute(
        select(BlogDraft).where(BlogDraft.id == draft_id)
    )
    old_draft = result.scalars().first()
    if not old_draft or not old_draft.keyword_ranking_id:
        return api_response(success=False, error="Original draft or ranking not found")

    # Archive old
    old_draft.status = "archived"

    # Generate new
    new_draft = await generate_draft(db, old_draft.keyword_ranking_id, model)
    return api_response(
        data=BlogDraftOut.model_validate(new_draft).model_dump()
    )


@router.delete("/{draft_id}")
async def delete_draft(draft_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a draft."""
    result = await db.execute(
        select(BlogDraft).where(BlogDraft.id == draft_id)
    )
    draft = result.scalars().first()
    if not draft:
        return api_response(success=False, error="Draft not found")
    
    await db.delete(draft)
    await db.commit()
    return api_response(data={"deleted": True})
