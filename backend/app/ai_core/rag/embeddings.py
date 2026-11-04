"""Embedding provider abstractions and test doubles.

Real providers are connected only via explicit authorization. Tests use the
TestEmbeddingProvider (deterministic, no external calls).
"""
from typing import Any, Dict, List
from uuid import UUID

from app.ai_core.models.provider import EmbeddingProvider


class TestEmbeddingProvider(EmbeddingProvider):
    """Deterministic test double: embeds text by hashing into a fixed vector."""

    name = "test"
    is_enabled = True

    def __init__(self, dim: int = 64):
        self.dim = dim

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    async def embed_query(self, text: str) -> List[float]:
        return self._vec(text)

    def _vec(self, text: str) -> List[float]:
        import hashlib

        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [(b / 255.0) for b in h[: self.dim]]
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]


class StubEmbeddingProvider(EmbeddingProvider):
    """Disabled provider used when no embedding provider is authorized."""

    name = "stub"
    is_enabled = False

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise RuntimeError("No embedding provider enabled")

    async def embed_query(self, text: str) -> List[float]:
        raise RuntimeError("No embedding provider enabled")
