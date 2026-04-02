"""Knowledge Base management API endpoints."""

import os
import uuid
import shutil
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db, async_session_factory
from app.core.security import get_current_user
from app.core.config import get_settings
from app.core.tiers import get_tier_limits, BASIC_EXTENSIONS
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase, Document, ProcessingStatus
from app.parsers import ParserFactory
from app.services.vector_store import VectorStoreService
from app.services.document_processor import DocumentProcessor
from app.api.schemas import KBCreate, KBUpdate, KBResponse, KBDetailResponse, DocumentResponse

settings = get_settings()
router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])
processor = DocumentProcessor()


@router.get("/", response_model=List[KBResponse])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all knowledge bases for the current user."""
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.owner_id == current_user.id)
        .order_by(KnowledgeBase.updated_at.desc())
    )
    kbs = result.scalars().all()
    return [KBResponse.model_validate(kb) for kb in kbs]


@router.post("/", response_model=KBResponse)
async def create_knowledge_base(
    data: KBCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base."""
    limits = get_tier_limits(current_user.tier)
    count_result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.owner_id == current_user.id)
    )
    existing_count = len(count_result.scalars().all())
    if existing_count >= limits.max_knowledge_bases:
        raise HTTPException(
            status_code=403,
            detail=f"已达到 {current_user.tier.upper()} 套餐知识库数量上限（{limits.max_knowledge_bases} 个）"
        )

    collection_name = f"kb_{current_user.id}_{uuid.uuid4().hex[:12]}"

    kb = KnowledgeBase(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        collection_name=collection_name,
    )
    db.add(kb)
    await db.flush()
    return KBResponse.model_validate(kb)


@router.get("/{kb_id}", response_model=KBDetailResponse)
async def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info about a knowledge base including documents."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    doc_result = await db.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    documents = doc_result.scalars().all()

    return KBDetailResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        document_count=kb.document_count,
        total_chunks=kb.total_chunks,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        documents=[DocumentResponse.model_validate(d) for d in documents],
    )


@router.put("/{kb_id}", response_model=KBResponse)
async def update_knowledge_base(
    kb_id: int,
    data: KBUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update knowledge base name or description."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if data.name is not None:
        kb.name = data.name
    if data.description is not None:
        kb.description = data.description
    kb.updated_at = datetime.utcnow()

    await db.flush()
    return KBResponse.model_validate(kb)


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge base and all its documents."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Delete vector collection
    VectorStoreService.delete_collection(kb.collection_name)

    # Delete uploaded files
    doc_result = await db.execute(select(Document).where(Document.kb_id == kb_id))
    for doc in doc_result.scalars().all():
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass

    await db.delete(kb)
    return {"message": "Knowledge base deleted successfully"}


@router.post("/{kb_id}/upload", response_model=List[DocumentResponse])
async def upload_documents(
    kb_id: int,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload one or more files to a knowledge base."""
    # Verify KB exists and belongs to user
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Check tier limits
    limits = get_tier_limits(current_user.tier)

    # Check document count limit
    doc_count_result = await db.execute(
        select(Document).where(Document.kb_id == kb_id)
    )
    existing_docs = len(doc_count_result.scalars().all())
    if existing_docs + len(files) > limits.max_docs_per_kb:
        raise HTTPException(
            status_code=403,
            detail=f"已达到 {current_user.tier.upper()} 套餐单知识库文档数上限（{limits.max_docs_per_kb} 个）"
        )

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(kb_id))
    os.makedirs(upload_dir, exist_ok=True)

    documents = []
    for file in files:
        # Validate file type
        file_type = ParserFactory.detect_file_type(file.filename)
        if not ParserFactory.get_parser(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}"
            )

        # Tier: check allowed file types for Free plan
        import os as _os
        ext = _os.path.splitext(file.filename)[1].lower()
        if current_user.tier == "free" and ext not in BASIC_EXTENSIONS:
            raise HTTPException(
                status_code=403,
                detail=f"FREE 套餐仅支持基础文件格式（TXT、PDF、Word），不支持 {ext} 文件"
            )

        # Validate file size
        content = await file.read()
        file_size = len(content)
        max_bytes = limits.max_file_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"文件 {file.filename} 超过 {current_user.tier.upper()} 套餐大小限制（{limits.max_file_size_mb}MB）"
            )

        # Save file
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_name)
        with open(file_path, "wb") as f:
            f.write(content)

        # Create document record
        doc = Document(
            kb_id=kb_id,
            filename=file.filename,
            file_type=file_type.value,
            file_size=file_size,
            file_path=file_path,
            status=ProcessingStatus.PENDING,
        )
        db.add(doc)
        await db.flush()
        documents.append(doc)

    await db.commit()

    # Process documents in background
    for doc in documents:
        background_tasks.add_task(_process_document_bg, doc.id)

    return [DocumentResponse.model_validate(d) for d in documents]


async def _process_document_bg(document_id: int):
    """Background task to process a document."""
    async with async_session_factory() as session:
        try:
            await processor.process_document(document_id, session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            # Update document status to failed
            result = await session.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = str(e)[:500]
                await session.commit()


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document from a knowledge base."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.owner_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    doc_result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.kb_id == kb_id)
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from vector store
    await VectorStoreService.delete_document_chunks(kb.collection_name, doc.id)

    # Remove file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)

    # Update KB stats
    kb.document_count = max(0, kb.document_count - 1)
    kb.total_chunks = max(0, kb.total_chunks - doc.chunk_count)

    return {"message": "Document deleted successfully"}


@router.get("/{kb_id}/documents/{doc_id}/status", response_model=DocumentResponse)
async def get_document_status(
    kb_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check the processing status of a document."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.kb_id == kb_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)
