"""RAG pipelines: high-level ingestion + retrieval orchestration."""
from typing import Any, Dict, Optional
from uuid import UUID

from app.ai_core.rag.chunking import chunk_text
from app.ai_core.rag.embeddings import EmbeddingProvider
from app.ai_core.rag.retrieval import RetrievalPipeline
from app.ai_core.rag.vector_store import VectorStore


class RAGOrchestrator:
    """Coordinates ingestion and retrieval for RAG."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        retrieval_pipeline: RetrievalPipeline,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.retrieval = retrieval_pipeline

    async def index_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embed_texts: List[str],
    ) -> None:
        """Embed chunks and add to vector store."""
        embeddings = await self.embedding_provider.embed_documents(embed_texts)
        chunk_ids = [c["chunk_id"] for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]
        await self.vector_store.add(chunk_ids, embeddings, metadatas)

    async def search(
        self,
        query: str,
        top_k: int = 10,
        subject: Optional[str] = None,
        language: Optional[str] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        return await self.retrieval.retrieve(
            query=query,
            top_k=top_k,
            subject=subject,
            language=language,
            document_ids=document_ids,
        )
