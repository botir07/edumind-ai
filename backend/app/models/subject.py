"""Subject model."""
import uuid

from typing import Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Subject(Base):
    """School subject (e.g. Mathematics, Uzbek language)."""

    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_subject_org_code"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # relationships
    topics: Mapped[list["Topic"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    class_subjects: Mapped[list["ClassSubject"]] = relationship(back_populates="subject", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Subject {self.name}>"
