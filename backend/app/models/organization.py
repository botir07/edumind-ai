"""Organization (school) model."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Organization(Base):
    """A school / organization. Multi-tenant root."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    timezone: Mapped[str] = mapped_column(String(60), nullable=False, default="Asia/Tashkent")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON text

    # relationships
    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    academic_years: Mapped[list["AcademicYear"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    students: Mapped[list["Student"]] = relationship(back_populates="organization")
    teachers: Mapped[list["Teacher"]] = relationship(back_populates="organization")
    parents: Mapped[list["Parent"]] = relationship(back_populates="organization")
    rooms: Mapped[list["Room"]] = relationship(back_populates="organization")
    learning_materials: Mapped[list["LearningMaterial"]] = relationship(
        back_populates="organization"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="organization")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="organization")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Organization {self.name}>"
