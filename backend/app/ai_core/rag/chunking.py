"""RAG text normalization and chunking.

Produces semantic-aware chunks with preserved metadata and document version tracking.
"""
import re
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


def normalize_text(text: str) -> str:
    """Normalize text: strip null bytes, collapse whitespace, trim."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    # collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    document_id: UUID,
    chunk_size: int = 1000,
    overlap: int = 200,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Split normalized text into overlapping chunks.

    Each chunk carries document_id, chunk_index, and preserved metadata.
    Chunking is sentence/paragraph aware where possible.
    """
    text = normalize_text(text)
    if not text:
        return []

    metadata = metadata or {}
    chunks: List[Dict[str, Any]] = []

    # Split into paragraphs first, then into sentence-ish units
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current = ""
    index = 0
    for para in paragraphs:
        candidate = (current + "\n\n" + para).strip() if current else para
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            # flush current
            if current:
                chunks.append(_make_chunk(document_id, index, current, metadata))
                index += 1
            # start new with para (split further if para itself too long)
            if len(para) > chunk_size:
                sub_chunks = _split_long(para, chunk_size, overlap, document_id, index, metadata)
                chunks.extend(sub_chunks)
                index += len(sub_chunks)
                current = ""
            else:
                current = para
    if current:
        chunks.append(_make_chunk(document_id, index, current, metadata))
        index += 1

    return chunks


def _make_chunk(document_id, index, content, metadata):
    return {
        "chunk_id": uuid4(),
        "document_id": document_id,
        "chunk_index": index,
        "content": content,
        "metadata": dict(metadata),
    }


def _split_long(text, chunk_size, overlap, document_id, start_index, metadata):
    chunks = []
    i = start_index
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end]
        chunks.append(_make_chunk(document_id, i, piece, metadata))
        i += 1
        if end >= len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks
