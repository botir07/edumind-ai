"""Room model."""
import uuid

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Room(Base):
    """Classroom / room."""

    __tablename__ = "rooms"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # relationships
    organization: Mapped["Organization"] = relationship(back_populates="rooms")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="room")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Room {self.name} org={self.organization_id}>"
