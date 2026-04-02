"""Share link API — generate/revoke guest access links."""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, verify_share_token
from app.models.user import User, ShareLink
from app.models.knowledge_base import KnowledgeBase
from app.core.tiers import get_tier_limits
from pydantic import BaseModel

router = APIRouter(prefix="/api/share", tags=["Share"])

SHARE_EXPIRE_HOURS = 1


class ShareLinkResponse(BaseModel):
    id: int
    token: str
    kb_id: int
    kb_name: str
    expires_at: datetime
    created_at: datetime
    url: str

    class Config:
        from_attributes = True


@router.post("/{kb_id}", response_model=ShareLinkResponse)
async def create_share_link(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a 1-hour guest share link for a knowledge base."""
    limits = get_tier_limits(current_user.tier)
    if not limits.can_share:
        raise HTTPException(
            status_code=403,
            detail=f"{current_user.tier.upper()} 套餐不支持分享链接，请升级到 Pro 或 Enterprise"
        )

    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    token = secrets.token_urlsafe(32)
    link = ShareLink(
        token=token,
        kb_id=kb_id,
        created_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(hours=SHARE_EXPIRE_HOURS),
    )
    db.add(link)
    await db.flush()

    return ShareLinkResponse(
        id=link.id,
        token=token,
        kb_id=kb_id,
        kb_name=kb.name,
        expires_at=link.expires_at,
        created_at=link.created_at,
        url=f"/guest?token={token}",
    )


@router.get("/{kb_id}", response_model=List[ShareLinkResponse])
async def list_share_links(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active share links for a knowledge base."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    links_result = await db.execute(
        select(ShareLink).where(
            ShareLink.kb_id == kb_id,
            ShareLink.expires_at > datetime.utcnow(),
        )
    )
    links = links_result.scalars().all()
    return [
        ShareLinkResponse(
            id=l.id, token=l.token, kb_id=kb_id, kb_name=kb.name,
            expires_at=l.expires_at, created_at=l.created_at,
            url=f"/guest?token={l.token}",
        )
        for l in links
    ]


@router.delete("/{link_id}")
async def revoke_share_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a share link."""
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.id == link_id,
            ShareLink.created_by == current_user.id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    await db.delete(link)
    return {"message": "分享链接已撤销"}


@router.get("/verify/{token}")
async def verify_link(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Verify a share token and return KB info (no auth required)."""
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    if link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="分享链接已过期")

    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == link.kb_id))
    kb = kb_result.scalar_one_or_none()

    return {
        "kb_id": link.kb_id,
        "kb_name": kb.name if kb else "",
        "kb_description": kb.description if kb else "",
        "expires_at": link.expires_at,
    }
