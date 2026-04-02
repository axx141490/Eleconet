"""Vector store service using ChromaDB and OpenAI Embeddings."""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from app.core.config import get_settings
from app.services.chunker import TextChunk

settings = get_settings()


class VectorStoreService:
    """Manage ChromaDB collections for knowledge base vector storage."""

    _client: Optional[chromadb.ClientAPI] = None

    @classmethod
    def get_client(cls) -> chromadb.ClientAPI:
        if cls._client is None:
            cls._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return cls._client

    @classmethod
    def get_embedding_function(cls):
        """Get embedding function based on current model config."""
        from app.services.llm_provider import get_embedding_function
        return get_embedding_function()

    @classmethod
    def get_or_create_collection(cls, collection_name: str):
        """Get or create a ChromaDB collection."""
        client = cls.get_client()
        return client.get_or_create_collection(
            name=collection_name,
            embedding_function=cls.get_embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )

    @classmethod
    def delete_collection(cls, collection_name: str):
        """Delete a ChromaDB collection."""
        client = cls.get_client()
        try:
            client.delete_collection(name=collection_name)
        except Exception:
            pass  # Collection may not exist

    @classmethod
    async def add_chunks(
        cls,
        collection_name: str,
        chunks: List[TextChunk],
        document_id: int,
    ) -> int:
        """Add text chunks to a ChromaDB collection. Returns number of chunks added."""
        if not chunks:
            return 0

        collection = cls.get_or_create_collection(collection_name)

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"doc_{document_id}_chunk_{i}"
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append({
                **chunk.metadata,
                "document_id": str(document_id),
                "chunk_index": str(i),
            })

        # Add in batches of 100
        batch_size = 100
        for start in range(0, len(ids), batch_size):
            end = min(start + batch_size, len(ids))
            collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        return len(chunks)

    @classmethod
    async def search(
        cls,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """Search for similar chunks in a collection."""
        collection = cls.get_or_create_collection(collection_name)

        count = collection.count()
        if count == 0:
            return []

        query_params = {
            "query_texts": [query],
            "n_results": min(top_k, count),
        }
        if filter_metadata:
            query_params["where"] = filter_metadata

        results = collection.query(**query_params)

        # Format results
        formatted = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "relevance_score": 1 - (results["distances"][0][i] if results["distances"] else 0),
                })

        return formatted

    @classmethod
    async def delete_document_chunks(cls, collection_name: str, document_id: int):
        """Remove all chunks for a specific document."""
        collection = cls.get_or_create_collection(collection_name)
        try:
            collection.delete(where={"document_id": str(document_id)})
        except Exception:
            pass

    @classmethod
    async def get_collection_stats(cls, collection_name: str) -> Dict:
        """Get statistics for a collection."""
        try:
            collection = cls.get_or_create_collection(collection_name)
            return {"count": collection.count(), "name": collection_name}
        except Exception:
            return {"count": 0, "name": collection_name}
