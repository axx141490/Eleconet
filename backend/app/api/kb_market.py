"""Knowledge Base Market / Template Library API."""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge_base import KBTemplate, KnowledgeBase
from app.core.tiers import get_tier_limits

router = APIRouter(prefix="/api/kb-market", tags=["KB Market"])


# ── Schemas ─────────────────────────────────────────────────────────────────

class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    category: str = "通用"
    tags: str = ""              # comma-separated
    sample_docs_hint: str = ""


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    sample_docs_hint: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    tags: str
    sample_docs_hint: str
    use_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active templates. Admins also see inactive ones."""
    query = select(KBTemplate).order_by(KBTemplate.category, KBTemplate.name)
    if not current_user.is_admin:
        query = query.where(KBTemplate.is_active == True)  # noqa: E712
    result = await db.execute(query)
    return [TemplateResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new template. Admin only."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可创建模板")
    tpl = KBTemplate(
        name=data.name,
        description=data.description,
        category=data.category,
        tags=data.tags,
        sample_docs_hint=data.sample_docs_hint,
        created_by=current_user.id,
    )
    db.add(tpl)
    await db.flush()
    return TemplateResponse.model_validate(tpl)


@router.put("/{tpl_id}", response_model=TemplateResponse)
async def update_template(
    tpl_id: int,
    data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a template. Admin only."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可编辑模板")
    result = await db.execute(select(KBTemplate).where(KBTemplate.id == tpl_id))
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tpl, field, value)
    tpl.updated_at = datetime.utcnow()
    await db.flush()
    return TemplateResponse.model_validate(tpl)


@router.delete("/{tpl_id}")
async def delete_template(
    tpl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a template. Admin only."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可删除模板")
    result = await db.execute(select(KBTemplate).where(KBTemplate.id == tpl_id))
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    await db.delete(tpl)
    return {"message": "模板已删除"}


@router.post("/{tpl_id}/use", response_model=dict)
async def use_template(
    tpl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base from a template for the current user."""
    result = await db.execute(
        select(KBTemplate).where(KBTemplate.id == tpl_id, KBTemplate.is_active == True)  # noqa: E712
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    # Check tier limits
    limits = get_tier_limits(current_user.tier)
    count_result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.owner_id == current_user.id)
    )
    existing_count = len(count_result.scalars().all())
    if existing_count >= limits.max_knowledge_bases:
        raise HTTPException(
            status_code=403,
            detail=f"已达到 {current_user.tier.upper()} 套餐知识库数量上限（{limits.max_knowledge_bases} 个）",
        )

    collection_name = f"kb_{current_user.id}_{uuid.uuid4().hex[:12]}"
    kb = KnowledgeBase(
        name=tpl.name,
        description=tpl.description,
        owner_id=current_user.id,
        collection_name=collection_name,
    )
    db.add(kb)

    tpl.use_count += 1
    tpl.updated_at = datetime.utcnow()

    await db.flush()
    return {
        "kb_id": kb.id,
        "name": kb.name,
        "sample_docs_hint": tpl.sample_docs_hint,
    }
