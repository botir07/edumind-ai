"""RAG Engine tests (run with pytest)."""
import asyncio
import pytest

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.rag.chunking import chunk_text, normalize_text
from app.ai_core.rag.citations import build_citations
from app.ai_core.rag.embeddings import TestEmbeddingProvider
from app.ai_core.rag.retrieval import RetrievalPipeline
from app.ai_core.rag.vector_store import TestVectorStore
from app.ai_core.models.provider import ScoredChunk
from uuid import uuid4


class FakeSession:
    def __init__(self, memberships):
        self.memberships = memberships
        self._expected_user_id = None
    async def execute(self, stmt):
        user_id = self._expected_user_id
        rows = [(m["organization_id"], m["role"]) for m in self.memberships if m["user_id"] == user_id and m["is_active"]]
        class R:
            def __init__(self, rows): self._rows = rows
            def all(self): return self._rows
        return R(rows)


def test_normalize_text():
    assert normalize_text("  hello   world  ") == "hello world"
    assert normalize_text("a\n\n\nb") == "a\n\nb"
    assert normalize_text("") == ""
    assert normalize_text("\x00hidden") == "hidden"


def test_chunk_text():
    doc_id = uuid4()
    text = "Para one.\n\nPara two is a bit longer sentence here. " * 10
    chunks = chunk_text(text, doc_id, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    for c in chunks:
        assert c["document_id"] == doc_id
        assert isinstance(c["chunk_index"], int)
        assert c["content"]


def test_citations_dedup():
    doc_a = uuid4()
    doc_b = uuid4()
    chunks = [
        {"document_id": doc_a, "source_title": "Doc A", "title": "Doc A", "subject": "Math"},
        {"document_id": doc_a, "source_title": "Doc A", "title": "Doc A", "subject": "Math"},
        {"document_id": doc_b, "source_title": "Doc B", "title": "Doc B", "subject": "Science"},
    ]
    cites = build_citations(chunks, max_citations=5)
    assert len(cites) == 2
    titles = {c["title"] for c in cites}
    assert titles == {"Doc A", "Doc B"}


@pytest.mark.asyncio
async def test_retrieval_org_isolation():
    doc_id = uuid4()
    org_a = uuid4()
    org_b = uuid4()
    user_a = uuid4()

    session = FakeSession([
        {"user_id": str(user_a), "organization_id": str(org_a), "role": "STUDENT", "is_active": True},
    ])
    session._expected_user_id = str(user_a)

    from app.ai_core.access_control.enforcement import AICoreEnforcer
    enforcer = AICoreEnforcer(session=session, user_id=str(user_a))

    ep = TestEmbeddingProvider(dim=32)
    vs = TestVectorStore()
    # add a chunk belonging to org_b
    await vs.add(
        chunk_ids=[uuid4()],
        embeddings=[await ep.embed_query("secret org b content")],
        metadatas=[{"document_id": str(doc_id), "organization_id": str(org_b), "title": "OrgB Doc", "subject": "Math", "language": "uz", "content": "secret org b content"}],
    )
    rp = RetrievalPipeline(embedding_provider=ep, vector_store=vs, enforcer=enforcer)
    result = await rp.retrieve(query="secret org b content", top_k=5)
    # org_b chunk should be filtered out (user_a not member of org_b)
    assert result["total_returned"] == 0, result
    print("RAG org isolation OK")


@pytest.mark.asyncio
async def test_retrieval_returns_org_chunk():
    doc_id = uuid4()
    org_a = uuid4()
    user_a = uuid4()

    session = FakeSession([
        {"user_id": str(user_a), "organization_id": str(org_a), "role": "STUDENT", "is_active": True},
    ])
    session._expected_user_id = str(user_a)

    from app.ai_core.access_control.enforcement import AICoreEnforcer
    enforcer = AICoreEnforcer(session=session, user_id=str(user_a))

    ep = TestEmbeddingProvider(dim=32)
    vs = TestVectorStore()
    await vs.add(
        chunk_ids=[uuid4()],
        embeddings=[await ep.embed_query("algebra basics")],
        metadatas=[{"document_id": str(doc_id), "organization_id": str(org_a), "title": "Algebra", "subject": "Math", "language": "uz", "content": "algebra basics"}],
    )
    rp = RetrievalPipeline(embedding_provider=ep, vector_store=vs, enforcer=enforcer)
    result = await rp.retrieve(query="algebra basics", top_k=5)
    assert result["total_returned"] >= 1, result
    assert result["citations"][0]["title"] == "Algebra"
    print("RAG org access OK")


if __name__ == "__main__":
    test_normalize_text()
    test_chunk_text()
    test_citations_dedup()
    asyncio.run(test_retrieval_org_isolation())
    asyncio.run(test_retrieval_returns_org_chunk())
    print("ALL RAG TESTS OK")
