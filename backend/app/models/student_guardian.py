"""Student guardian relationship model."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class StudentGuardian(Base):
    """Verified guardian relationship between a parent and a student."""

    __tablename__ = "student_guardians"
    __table_args__ = (
        UniqueConstraint("student_id", "parent_id", name="uq_guardian_student_parent"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parents.id", ondelete="CASCADE"), nullable=False
    )
    guardian_relationship: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    student: Mapped["Student"] = relationship(back_populates="guardians")
    parent: Mapped["Parent"] = relationship(back_populates="guardianships")
    verifier: Mapped[Optional["User"]] = relationship(foreign_keys=[verified_by])

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<StudentGuardian student={self.student_id} parent={self.parent_id} "
            f"verified={self.is_verified}>"
        )
