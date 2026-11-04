"""AI Core shared models: provider, request, response."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# ---------- Provider abstractions (plain abstract classes, not Pydantic) ----------

class ModelProvider:
    """Abstract interface for a language model provider. Not tied to any vendor."""

    name: str = "base"
    is_enabled: bool = False

    async def generate(self, request: "ModelRequest") -> "ModelResponse":
        raise NotImplementedError

    async def health_check(self) -> bool:
        raise NotImplementedError


class EmbeddingProvider:
    """Abstract interface for an embedding provider."""

    name: str = "base"
    is_enabled: bool = False

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    async def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError


class VectorStore:
    """Abstract interface for a vector store."""

    name: str = "base"
    is_enabled: bool = False

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
    ) -> List["ScoredChunk"]:
        raise NotImplementedError

    async def delete(self, document_id: UUID) -> None:
        raise NotImplementedError


# ---------- Request / Response (Pydantic) ----------

class ModelRequest(BaseModel):
    """Request sent to a Model Provider Adapter."""

    messages: List[Dict[str, str]]  # [{role, content}]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = False
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Response from a Model Provider Adapter."""

    content: str
    model: Optional[str] = None
    provider: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)  # token counts if available
    finish_reason: Optional[str] = None
    latency_ms: Optional[int] = None


class ScoredChunk(BaseModel):
    """A retrieved document chunk with score and metadata."""

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_title: Optional[str] = None
    subject: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
