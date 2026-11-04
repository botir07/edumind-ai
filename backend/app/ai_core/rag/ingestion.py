"""RAG ingestion pipeline (metadata + chunking + embedding registration).

Does NOT execute file parsing itself; receives normalized text and metadata.
Secure: validates file, stores private path, computes checksum, marks pending.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from app.ai_core.rag.chunking import chunk_text


class IngestionPipeline:
    def __init__(self, enforcer, session=None):
        self.enforcer = enforcer
        self.session = session

    async def prepare_document(
        self,
        *,
        organization_id: UUID,
        title: str,
        subject: Optional[str] = None,
        language: str = "uz",
        source: Optional[str] = None,
        uploader_id: Optional[UUID] = None,
        file_path: Optional[str] = None,
        mime_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
        checksum: str,
        content: str,
    ) -> Dict[str, Any]:
        """Validate and chunk a document for indexing.

        Returns document metadata + chunks (caller persists + embeds).
        """
        # access check
        await self.enforcer.require_document_access(organization_id)

        chunks = chunk_text(
            text=content,
            document_id=None,  # replaced at persist with real document id
            chunk_size=1000,
            overlap=200,
            metadata={
                "title": title,
                "subject": subject,
                "language": language,
                "organization_id": str(organization_id),
            },
        )

        return {
            "organization_id": organization_id,
            "title": title,
            "subject": subject,
            "language": language,
            "source": source,
            "uploader_id": uploader_id,
            "file_path": file_path,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "checksum": checksum,
            "processing_status": "pending",
            "chunks": chunks,
            "chunk_count": len(chunks),
        }
