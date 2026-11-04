"""Class-subject assignment model."""
import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ClassSubject(Base):
    """A subject taught in a class by a teacher for an academic year."""

    __tablename__ = "class_subjects"
    __table_args__ = (
        UniqueConstraint("class_id", "subject_id", "academic_year_id", name="uq_class_subject_year"),
    )

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )

    # relationships
    class_: Mapped["Class"] = relationship(back_populates="class_subjects")
    subject: Mapped["Subject"] = relationship(back_populates="class_subjects")
    teacher: Mapped["Teacher"] = relationship(back_populates="class_subjects")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="class_subject", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ClassSubject class={self.class_id} subject={self.subject_id}>"
