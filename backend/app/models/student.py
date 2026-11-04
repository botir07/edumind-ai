"""Student model."""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Student(Base):
    """Student profile linked to a user account."""

    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("student_number", "organization_id", name="uq_student_number_org"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    student_number: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    # relationships
    user: Mapped["User"] = relationship(back_populates="student_profile")
    organization: Mapped["Organization"] = relationship(back_populates="students")
    enrollments: Mapped[list["ClassEnrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    guardians: Mapped[list["StudentGuardian"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    grades: Mapped[list["Grade"]] = relationship(back_populates="student")
    submissions: Mapped[list["AssignmentSubmission"]] = relationship(back_populates="student")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="student")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Student {self.student_number} org={self.organization_id}>"
