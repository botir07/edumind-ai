"""Grade record model (gradebook)."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Grade(Base):
    """A student's score on an assessment."""

    __tablename__ = "grade_records"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    assessment: Mapped["Assessment"] = relationship(back_populates="grades")
    student: Mapped["Student"] = relationship(back_populates="grades")
    history: Mapped[list["GradeHistory"]] = relationship(back_populates="grade", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Grade assessment={self.assessment_id} student={self.student_id} score={self.score}>"
