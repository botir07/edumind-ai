"""Vector store abstractions and adapters.

Primary candidate: PostgreSQL + pgvector. Since pgvector availability must be
confirmed per environment, a TestVectorStore (in-memory cosine similarity) is
provided for tests and a PgVectorStore adapter for production.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.ai_core.models.provider import ScoredChunk, VectorStore


class TestVectorStore(VectorStore):
    """In-memory vector store with cosine similarity for tests."""

    name = "test"
    is_enabled = True

    def __init__(self):
        self._chunks: Dict[UUID, Dict[str, Any]] = {}
        self._vectors: Dict[UUID, List[float]] = {}

    async def add(
        self,
        chunk_ids: List[UUID],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        for cid, emb, meta in zip(chunk_ids, embeddings, metadatas):
            self._vectors[cid] = emb
            self._chunks[cid] = meta

    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List[ScoredChunk]:
        import math

        def cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a)) or 1.0
            nb = math.sqrt(sum(y * y for y in b)) or 1.0
            return dot / (na * nb)

        scored = []
        for cid, emb in self._vectors.items():
            meta = self._chunks.get(cid, {})
            if filters and not self._matches(meta, filters):
                continue
            score = cosine(query_embedding, emb)
            scored.append(ScoredChunk(
                chunk_id=cid,
                document_id=UUID(meta.get("document_id", str(cid))),
                content=meta.get("content", ""),
                score=score,
                metadata=meta,
                source_title=meta.get("title"),
                subject=meta.get("subject"),
                page=meta.get("page"),
                section=meta.get("section"),
            ))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]

    async def delete(self, document_id: UUID) -> None:
        to_delete = [cid for cid, m in self._chunks.items() if m.get("document_id") == str(document_id)]
        for cid in to_delete:
            self._vectors.pop(cid, None)
            self._chunks.pop(cid, None)

    @staticmethod
    def _matches(meta: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for k, v in filters.items():
            if k == "organization_id__in":
                if meta.get("organization_id") not in v:
                    return False
            elif meta.get(k) != v:
                return False
        return True


class PgVectorStore(VectorStore):
    """PostgreSQL + pgvector vector store adapter.

    Requires the pgvector extension on the PostgreSQL database. Raises a clear
    error if unavailable, allowing callers to fall back to TestVectorStore.
    """

    name = "pgvector"
    is_enabled = False  # enabled only after health check confirms extension

    def __init__(self, session):
        self.session = session

    async def health_check(self) -> bool:
        try:
            from sqlalchemy import text
            await self.session.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector'"))
            return True
        except Exception:
            return False

    async def add(
        self,
        chunk_ids: List[UUID],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        raise NotImplementedError("PgVectorStore.add not yet wired to ai_document_chunks")

    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List[ScoredChunk]:
        raise NotImplementedError("PgVectorStore.search not yet wired")

    async def delete(self, document_id: UUID) -> None:
        raise NotImplementedError("PgVectorStore.delete not yet wired")
