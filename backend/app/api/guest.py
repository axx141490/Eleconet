"""Guest Q&A API — no login required, uses share token."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.models.user import ShareLink
from app.models.knowledge_base import KnowledgeBase
from app.services.rag_engine import RAGEngine
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/api/guest", tags=["Guest"])
rag_engine = RAGEngine()


class GuestChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    token: str
    top_k: int = Field(default=5, ge=1, le=20)
    temperature: float = Field(default=0.7, ge=0, le=2)


class GuestChatResponse(BaseModel):
    answer: str
    sources: List[dict]


async def _get_share_link(token: str, db: AsyncSession) -> ShareLink:
    result = await db.execute(select(ShareLink).where(ShareLink.token == token))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    if link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="分享链接已过期")
    return link


@router.get("/kb")
async def get_guest_kb(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get KB info via share token (no auth)."""
    link = await _get_share_link(token, db)
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == link.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {
        "kb_id": kb.id,
        "kb_name": kb.name,
        "kb_description": kb.description,
        "expires_at": link.expires_at,
    }


@router.post("/chat", response_model=GuestChatResponse)
async def guest_chat(
    request: GuestChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Q&A for guests via share token."""
    link = await _get_share_link(request.token, db)

    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == link.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    result = await rag_engine.query(
        question=request.question,
        collection_name=kb.collection_name,
        top_k=request.top_k,
        temperature=request.temperature,
    )
    return GuestChatResponse(answer=result["answer"], sources=result["sources"])
