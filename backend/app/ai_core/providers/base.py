"""Abstract provider interfaces for AI Core.

These are protocol-style abstract base classes. Concrete adapters (test doubles,
pgvector vector store, future real model providers) implement these without
changing the AI Core orchestration layer.

No concrete provider is enabled by default. A real Model Provider is connected
only via explicit authorization (Phase 3+).
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.ai_core.models.provider import EmbeddingProvider as _EP
from app.ai_core.models.provider import ModelProvider as _MP
from app.ai_core.models.provider import VectorStore as _VS


class ModelProvider(_MP):
    """Abstract language model provider interface."""

    async def generate(self, request: "ModelRequest") -> "ModelResponse":  # type: ignore[name-defined]
        raise NotImplementedError

    async def health_check(self) -> bool:
        raise NotImplementedError


class EmbeddingProvider(_EP):
    """Abstract embedding provider interface."""

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    async def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError


class VectorStore(_VS):
    """Abstract vector store interface."""

    async def add(
        self,
        chunk_ids: List[UUID],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        raise NotImplementedError

    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List["ScoredChunk"]:  # type: ignore[name-defined]
        raise NotImplementedError

    async def delete(self, document_id: UUID) -> None:
        raise NotImplementedError


__all__ = ["ModelProvider", "EmbeddingProvider", "VectorStore"]
