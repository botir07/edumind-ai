"""RAG citation building."""
from typing import Any, Dict, List, Optional


def build_citations(
    chunks: List[Dict[str, Any]],
    max_citations: int = 5,
) -> List[Dict[str, Any]]:
    """Build citation list from retrieved chunks.

    Each citation: document_id, title, subject, page/section.
    Never fabricates sources.
    """
    citations: List[Dict[str, Any]] = []
    seen = set()
    for c in chunks:
        doc_id = c.get("document_id")
        title = c.get("source_title") or c.get("title") or "Unknown document"
        key = (str(doc_id), title)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "document_id": str(doc_id) if doc_id else None,
                "title": title,
                "subject": c.get("subject"),
                "page": c.get("page"),
                "section": c.get("section"),
            }
        )
        if len(citations) >= max_citations:
            break
    return citations
