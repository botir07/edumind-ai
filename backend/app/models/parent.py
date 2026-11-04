"""Parent model."""
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Parent(Base):
    """Parent/guardian account linked to a user account."""

    __tablename__ = "parents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship(back_populates="parent_profile")
    organization: Mapped["Organization"] = relationship(back_populates="parents")
    guardianships: Mapped[list["StudentGuardian"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Parent user={self.user_id} org={self.organization_id}>"
