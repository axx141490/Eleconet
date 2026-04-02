"""Document processing service - orchestrates parsing, chunking, and vectorization."""

import os
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge_base import Document, KnowledgeBase, ProcessingStatus
from app.parsers import ParserFactory
from app.services.chunker import TextChunker
from app.services.vector_store import VectorStoreService
from app.core.config import get_settings

settings = get_settings()


class DocumentProcessor:
    """Process uploaded documents: parse → chunk → embed → store."""

    def __init__(self):
        self.chunker = TextChunker()

    async def process_document(self, document_id: int, db: AsyncSession) -> bool:
        """
        Process a single document end-to-end.

        Steps:
        1. Parse the file using the appropriate parser
        2. Split text into chunks
        3. Generate embeddings and store in ChromaDB
        4. Update document status in database
        """
        # Get document from DB
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return False

        # Get knowledge base for collection name
        kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
        kb = kb_result.scalar_one_or_none()
        if not kb:
            return False

        try:
            # Update status to processing
            doc.status = ProcessingStatus.PROCESSING
            await db.commit()

            # Step 1: Parse the file
            parsed_chunks = await ParserFactory.parse_file(doc.file_path, doc.filename)

            if not parsed_chunks:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = "No content could be extracted from the file"
                await db.commit()
                return False

            # Step 2: Chunk the parsed text
            all_chunks = []
            for parsed in parsed_chunks:
                chunks = self.chunker.split_text(parsed.text, parsed.metadata)
                all_chunks.extend(chunks)

            if not all_chunks:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = "Text chunking produced no results"
                await db.commit()
                return False

            # Step 3: Store chunks in vector DB
            chunk_count = await VectorStoreService.add_chunks(
                collection_name=kb.collection_name,
                chunks=all_chunks,
                document_id=doc.id,
            )

            # Step 4: Update document and knowledge base stats
            doc.status = ProcessingStatus.COMPLETED
            doc.chunk_count = chunk_count
            doc.processed_at = datetime.utcnow()
            doc.error_message = None

            kb.document_count = await self._count_documents(db, kb.id)
            kb.total_chunks = await self._count_chunks(db, kb.id)

            await db.commit()
            return True

        except Exception as e:
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)[:500]
            await db.commit()
            return False

    async def _count_documents(self, db: AsyncSession, kb_id: int) -> int:
        result = await db.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                Document.status == ProcessingStatus.COMPLETED
            )
        )
        return len(result.scalars().all())

    async def _count_chunks(self, db: AsyncSession, kb_id: int) -> int:
        result = await db.execute(
            select(Document).where(
                Document.kb_id == kb_id,
                Document.status == ProcessingStatus.COMPLETED
            )
        )
        docs = result.scalars().all()
        return sum(d.chunk_count for d in docs)
