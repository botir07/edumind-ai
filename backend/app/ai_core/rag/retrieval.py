"""RAG retrieval pipeline with organization-scoped access control.

Steps:
  1. Receive query + user context
  2. Resolve organization scope (server-side)
  3. Normalize query + detect language
  4. Embed query
  5. Vector search with metadata + org filtering
  6. Access check per chunk (document org membership)
  7. Rank + trim to top_k
  8. Build context + citations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.rag.chunking import normalize_text
from app.ai_core.rag.embeddings import EmbeddingProvider
from app.ai_core.rag.vector_store import VectorStore
from app.ai_core.models.provider import ScoredChunk


class RetrievalPipeline:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        enforcer: AICoreEnforcer,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.enforcer = enforcer

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        subject: Optional[str] = None,
        language: Optional[str] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """Retrieve access-checked chunks for a query.

        Returns {chunks, citations, total_returned, query_hash}.
        """
        # resolve org scope
        org_ids = await self.enforcer.org_ids()
        if not org_ids:
            return {"chunks": [], "citations": [], "total_returned": 0, "query_hash": ""}

        # cap top_k
        max_k = await self.enforcer.max_top_k()
        top_k = min(top_k, max_k)

        # normalize + embed
        norm_query = normalize_text(query)
        if not norm_query:
            return {"chunks": [], "citations": [], "total_returned": 0, "query_hash": ""}

        query_embedding = await self.embedding_provider.embed_query(norm_query)

        # build filters
        filters: Dict[str, Any] = {}
        if subject:
            filters["subject"] = subject
        if language:
            filters["language"] = language
        # org filter: chunks belong to documents in allowed orgs
        filters["organization_id__in"] = [str(o) for o in org_ids]

        raw_results = await self.vector_store.search(query_embedding, filters=filters, top_k=top_k * 2)

        # per-chunk document access check
        chunks: List[ScoredChunk] = []
        for r in raw_results:
            doc_org = r.metadata.get("organization_id")
            if doc_org and not await self.enforcer.can_access_org(doc_org):
                continue
            chunks.append(r)
            if len(chunks) >= top_k:
                break

        citations = self._build_citations(chunks)
        query_hash = self._hash(norm_query)

        return {
            "chunks": [c.model_dump() for c in chunks],
            "citations": citations,
            "total_returned": len(chunks),
            "query_hash": query_hash,
        }

    @staticmethod
    def _build_citations(chunks: List[ScoredChunk]) -> List[Dict[str, Any]]:
        citations = []
        seen = set()
        for c in chunks:
            key = (str(c.document_id), c.source_title)
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                {
                    "document_id": str(c.document_id),
                    "title": c.source_title,
                    "subject": c.subject,
                    "page": c.page,
                    "section": c.section,
                }
            )
        return citations

    @staticmethod
    def _hash(text: str) -> str:
        import hashlib

        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
