"""Lesson model (timetable)."""
import uuid
from sqlalchemy import ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Lesson(Base):
    """A timetable lesson."""

    __tablename__ = "lessons"

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=False
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True
    )
    day_of_week: Mapped[int] = mapped_column(nullable=False)  # 1=Mon ... 7=Sun
    start_time: Mapped[str] = mapped_column(Time, nullable=False)  # stored as time
    end_time: Mapped[str] = mapped_column(Time, nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    is_cancelled: Mapped[bool] = mapped_column(nullable=False, default=False)
    replacement_teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )

    # relationships
    class_: Mapped["Class"] = relationship(back_populates="lessons")
    subject: Mapped["Subject"] = relationship()
    teacher: Mapped["Teacher"] = relationship(foreign_keys=[teacher_id], back_populates="lessons")
    room: Mapped["Room"] = relationship(back_populates="lessons")
    replacement_teacher: Mapped["Teacher"] = relationship(foreign_keys=[replacement_teacher_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Lesson {self.day_of_week} {self.start_time}-{self.end_time}>"
