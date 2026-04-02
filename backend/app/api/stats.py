"""System statistics API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase, Document
from app.models.conversation import Conversation
from app.parsers import ParserFactory
from app.api.schemas import SystemStats

router = APIRouter(prefix="/api/stats", tags=["Statistics"])


@router.get("/", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics (admin) or user-specific stats."""
    if current_user.is_admin:
        users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
        kb_count = (await db.execute(select(func.count(KnowledgeBase.id)))).scalar() or 0
        doc_count = (await db.execute(select(func.count(Document.id)))).scalar() or 0
        conv_count = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    else:
        users_count = 1
        kb_count = (await db.execute(
            select(func.count(KnowledgeBase.id)).where(KnowledgeBase.owner_id == current_user.id)
        )).scalar() or 0
        doc_count = (await db.execute(
            select(func.count(Document.id)).join(KnowledgeBase).where(KnowledgeBase.owner_id == current_user.id)
        )).scalar() or 0
        conv_count = (await db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == current_user.id)
        )).scalar() or 0

    return SystemStats(
        total_users=users_count,
        total_knowledge_bases=kb_count,
        total_documents=doc_count,
        total_conversations=conv_count,
        supported_formats=ParserFactory.get_supported_extensions(),
    )
