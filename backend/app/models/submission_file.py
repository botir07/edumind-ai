"""Submission file model."""
import uuid

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SubmissionFile(Base):
    """File attached to a submission."""

    __tablename__ = "submission_files"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # sanitized stored name
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)  # private path, not public
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    submission: Mapped["AssignmentSubmission"] = relationship(back_populates="files")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SubmissionFile {self.filename}>"
