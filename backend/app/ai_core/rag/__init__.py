"""RAG Engine package."""
from app.ai_core.rag.chunking import chunk_text, normalize_text  # noqa: F401
from app.ai_core.rag.retrieval import RetrievalPipeline  # noqa: F401
from app.ai_core.rag.citations import build_citations  # noqa: F401

__all__ = ["chunk_text", "normalize_text", "RetrievalPipeline", "build_citations"]
