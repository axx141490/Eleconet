"""Chat / Q&A API endpoints with streaming support."""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tiers import get_tier_limits
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.conversation import Conversation, Message
from app.services.rag_engine import RAGEngine
from app.api.schemas import (
    ChatRequest, ChatResponse, ConversationResponse,
    ConversationDetailResponse, MessageResponse,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])
rag_engine = RAGEngine()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a question and get a RAG-powered answer."""
    # Verify knowledge base
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == request.kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Get or create conversation
    conversation = None
    chat_history = []

    if request.conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Load chat history
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()
        chat_history = [{"role": m.role, "content": m.content} for m in messages]

    if not conversation:
        # Check conversation history limit for the tier
        limits = get_tier_limits(current_user.tier)
        conv_count_result = await db.execute(
            select(Conversation).where(Conversation.user_id == current_user.id)
        )
        conv_count = len(conv_count_result.scalars().all())
        if conv_count >= limits.max_conversations:
            # Delete oldest conversation to make room
            oldest_result = await db.execute(
                select(Conversation)
                .where(Conversation.user_id == current_user.id)
                .order_by(Conversation.updated_at.asc())
                .limit(1)
            )
            oldest = oldest_result.scalar_one_or_none()
            if oldest:
                await db.delete(oldest)

        conversation = Conversation(
            user_id=current_user.id,
            kb_id=request.kb_id,
            title=request.question[:80],
        )
        db.add(conversation)
        await db.flush()

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.question,
    )
    db.add(user_msg)
    await db.flush()

    # RAG query
    result = await rag_engine.query(
        question=request.question,
        collection_name=kb.collection_name,
        top_k=request.top_k,
        chat_history=chat_history,
        temperature=request.temperature,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        sources=result["sources"],
    )
    db.add(assistant_msg)
    await db.flush()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a RAG-powered answer using Server-Sent Events."""
    # Verify knowledge base
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == request.kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Load chat history if conversation exists
    chat_history = []
    if request.conversation_id:
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == request.conversation_id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()
        chat_history = [{"role": m.role, "content": m.content} for m in messages]

    async def generate():
        async for chunk in rag_engine.query_stream(
            question=request.question,
            collection_name=kb.collection_name,
            top_k=request.top_k,
            chat_history=chat_history,
            temperature=request.temperature,
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ─── Conversation Management ──────────────────────────────

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return [ConversationResponse.model_validate(c) for c in convs]


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    response = ConversationDetailResponse.model_validate(conv)
    response.messages = [MessageResponse.model_validate(m) for m in messages]
    return response


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    return {"message": "Conversation deleted"}
