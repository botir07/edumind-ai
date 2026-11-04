"""Grade history model (audit of grade changes)."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GradeHistory(Base):
    """Immutable audit record of grade score changes."""

    __tablename__ = "grade_history"

    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grade_records.id", ondelete="CASCADE"), nullable=False
    )
    old_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    new_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    grade: Mapped["Grade"] = relationship(back_populates="history")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<GradeHistory grade={self.grade_id} old={self.old_score} new={self.new_score}>"
