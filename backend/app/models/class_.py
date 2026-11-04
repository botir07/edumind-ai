"""Class model."""
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Class(Base):
    """A school class (e.g. 5-A)."""

    __tablename__ = "classes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grade_levels.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    room_teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # relationships
    organization: Mapped["Organization"] = relationship()
    grade: Mapped[Optional["GradeLevel"]] = relationship(back_populates="classes")
    room_teacher: Mapped[Optional["Teacher"]] = relationship(foreign_keys=[room_teacher_id])
    enrollments: Mapped[list["ClassEnrollment"]] = relationship(
        back_populates="class_", cascade="all, delete-orphan"
    )
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="class_")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="class_")
    class_subjects: Mapped[list["ClassSubject"]] = relationship(
        back_populates="class_", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Class {self.name} org={self.organization_id}>"
