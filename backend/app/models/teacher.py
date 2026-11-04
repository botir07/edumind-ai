"""Teacher model."""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.lesson import Lesson  # noqa: F401


class Teacher(Base):
    """Teacher profile linked to a user account."""

    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("employee_number", "organization_id", name="uq_employee_number_org"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    employee_number: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_specialization: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    # relationships
    user: Mapped["User"] = relationship(back_populates="teacher_profile")
    organization: Mapped["Organization"] = relationship(back_populates="teachers")
    class_subjects: Mapped[list["ClassSubject"]] = relationship(back_populates="teacher")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="teacher", foreign_keys=[Lesson.teacher_id]
    )
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="teacher")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Teacher {self.employee_number} org={self.organization_id}>"
