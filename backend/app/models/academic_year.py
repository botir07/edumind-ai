"""Academic year model."""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AcademicYear(Base):
    """Configurable academic period for an organization."""

    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_academic_year_org_name"),
        Index(
            "uq_academic_year_org_current",
            "organization_id",
            unique=True,
            postgresql_where=text("is_current = true"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # relationships
    organization: Mapped["Organization"] = relationship(back_populates="academic_years")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AcademicYear {self.name} org={self.organization_id}>"
