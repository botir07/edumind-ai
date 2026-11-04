"""Grade level model (e.g. 1st grade, 2nd grade)."""
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GradeLevel(Base):
    """Grade / year level within an organization (not to be confused with gradebook grades)."""

    __tablename__ = "grade_levels"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_grade_level_org_name"),
        UniqueConstraint("organization_id", "level_order", name="uq_grade_level_org_order"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    level_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # relationships
    organization: Mapped["Organization"] = relationship()
    classes: Mapped[list["Class"]] = relationship(back_populates="grade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<GradeLevel {self.name} order={self.level_order}>"
