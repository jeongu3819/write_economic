"""Prompts router."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.prompt_template import PromptTemplate
from app.schemas.prompts import PromptCreateRequest, PromptUpdateRequest, PromptTemplateOut
from app.utils.response import api_response

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("")
async def list_prompts(db: AsyncSession = Depends(get_db)):
    """List all prompt templates."""
    result = await db.execute(
        select(PromptTemplate).order_by(PromptTemplate.template_type, PromptTemplate.version.desc())
    )
    prompts = result.scalars().all()
    return api_response(
        data=[PromptTemplateOut.model_validate(p).model_dump() for p in prompts]
    )


@router.post("")
async def create_prompt(body: PromptCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new prompt template."""
    # Find max version for this type
    result = await db.execute(
        select(PromptTemplate)
        .where(PromptTemplate.template_type == body.template_type)
        .order_by(PromptTemplate.version.desc())
    )
    existing = result.scalars().first()
    next_version = (existing.version + 1) if existing else 1

    prompt = PromptTemplate(
        template_name=body.template_name,
        template_type=body.template_type,
        version=next_version,
        system_prompt=body.system_prompt,
        schema_json=body.schema_json,
        is_active=True,
    )

    # Deactivate previous versions
    if existing:
        all_result = await db.execute(
            select(PromptTemplate)
            .where(PromptTemplate.template_type == body.template_type)
        )
        for old in all_result.scalars().all():
            old.is_active = False

    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)

    return api_response(
        data=PromptTemplateOut.model_validate(prompt).model_dump()
    )


@router.patch("/{prompt_id}")
async def update_prompt(
    prompt_id: int,
    body: PromptUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a prompt template."""
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.id == prompt_id)
    )
    prompt = result.scalars().first()
    if not prompt:
        return api_response(success=False, error="Prompt not found")

    if body.template_name is not None:
        prompt.template_name = body.template_name
    if body.system_prompt is not None:
        prompt.system_prompt = body.system_prompt
    if body.schema_json is not None:
        prompt.schema_json = body.schema_json
    if body.is_active is not None:
        prompt.is_active = body.is_active

    await db.commit()
    await db.refresh(prompt)

    return api_response(
        data=PromptTemplateOut.model_validate(prompt).model_dump()
    )
