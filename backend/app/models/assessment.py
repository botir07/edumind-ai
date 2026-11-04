"""Assessment model (gradebook)."""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Assessment(Base):
    """An assessment (quiz, exam, homework, etc.) for a class-subject."""

    __tablename__ = "assessments"

    class_subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_subjects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # quiz/exam/homework/participation
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=100)
    weight: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=1)
    date_assigned: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )

    # relationships
    class_subject: Mapped["ClassSubject"] = relationship(back_populates="assessments")
    grades: Mapped[list["Grade"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Assessment {self.title}>"
