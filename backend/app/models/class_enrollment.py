"""Class enrollment model."""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ClassEnrollment(Base):
    """Enrollment of a student in a class for an academic year."""

    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "class_id", "academic_year_id", name="uq_enrollment_student_class_year"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    enrolled_at: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    # relationships
    student: Mapped["Student"] = relationship(back_populates="enrollments")
    class_: Mapped["Class"] = relationship(back_populates="enrollments")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ClassEnrollment student={self.student_id} class={self.class_id}>"
