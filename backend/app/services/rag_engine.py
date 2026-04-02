"""RAG (Retrieval-Augmented Generation) engine for intelligent Q&A."""

from typing import List, Dict, Optional, AsyncGenerator
from app.services.vector_store import VectorStoreService
from app.services.llm_provider import get_llm_client, get_llm_model


class RAGEngine:
    """Core RAG engine combining retrieval and generation."""

    async def query(
        self,
        question: str,
        collection_name: str,
        top_k: int = 5,
        chat_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
    ) -> Dict:
        """
        Execute a RAG query: retrieve relevant chunks then generate an answer.

        Returns:
            Dict with 'answer', 'sources', and 'context_used'
        """
        # Step 1: Retrieve relevant documents
        search_results = await VectorStoreService.search(
            collection_name=collection_name,
            query=question,
            top_k=top_k,
        )

        if not search_results:
            return {
                "answer": "I couldn't find relevant information in the knowledge base to answer your question. Please try rephrasing or make sure the relevant documents have been uploaded.",
                "sources": [],
                "context_used": [],
            }

        # Step 2: Build context from retrieved chunks
        context_parts = []
        sources = []
        for i, result in enumerate(search_results):
            context_parts.append(f"[Document {i+1}] (Relevance: {result['relevance_score']:.2f})\n{result['text']}")
            sources.append({
                "document": result["metadata"].get("source", "Unknown"),
                "relevance_score": round(result["relevance_score"], 3),
                "chunk_index": result["metadata"].get("chunk_index", "0"),
                "file_type": result["metadata"].get("file_type", "unknown"),
            })

        context = "\n\n---\n\n".join(context_parts)

        # Step 3: Build messages for LLM
        system_prompt = """You are a knowledgeable assistant that answers questions based on the provided context from a knowledge base.

Rules:
1. Answer based ONLY on the provided context. If the context doesn't contain enough information, say so clearly.
2. Cite which document(s) you're referencing in your answer using [Document N] notation.
3. If the question is in Chinese, answer in Chinese. If in English, answer in English. Match the user's language.
4. Be concise but thorough. Provide specific details from the context.
5. If multiple documents provide relevant information, synthesize them into a coherent answer.
6. Never make up information not present in the context."""

        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history for multi-turn conversation
        if chat_history:
            for msg in chat_history[-6:]:  # Keep last 3 exchanges
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add user question with context
        user_message = f"""Context from knowledge base:

{context}

---

Question: {question}"""

        messages.append({"role": "user", "content": user_message})

        # Step 4: Generate answer using LLM
        response = get_llm_client().chat.completions.create(
            model=get_llm_model(),
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "sources": sources,
            "context_used": [r["text"][:200] + "..." for r in search_results],
        }

    async def query_stream(
        self,
        question: str,
        collection_name: str,
        top_k: int = 5,
        chat_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator:
        """Stream a RAG query response."""
        # Retrieve relevant documents
        search_results = await VectorStoreService.search(
            collection_name=collection_name,
            query=question,
            top_k=top_k,
        )

        sources = []
        if not search_results:
            yield {"type": "answer", "content": "I couldn't find relevant information in the knowledge base."}
            yield {"type": "sources", "content": []}
            yield {"type": "done", "content": ""}
            return

        context_parts = []
        for i, result in enumerate(search_results):
            context_parts.append(f"[Document {i+1}] (Relevance: {result['relevance_score']:.2f})\n{result['text']}")
            sources.append({
                "document": result["metadata"].get("source", "Unknown"),
                "relevance_score": round(result["relevance_score"], 3),
                "file_type": result["metadata"].get("file_type", "unknown"),
            })

        context = "\n\n---\n\n".join(context_parts)

        system_prompt = """You are a knowledgeable assistant that answers questions based on the provided context from a knowledge base.
Answer based ONLY on the provided context. Cite sources using [Document N] notation. Match the user's language."""

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})

        # Stream response
        stream = get_llm_client().chat.completions.create(
            model=get_llm_model(),
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield {"type": "answer", "content": chunk.choices[0].delta.content}

        yield {"type": "sources", "content": sources}
        yield {"type": "done", "content": ""}
