"""Topic model."""
import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Topic(Base):
    """Topic within a subject (curriculum unit)."""

    __tablename__ = "topics"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # relationships
    subject: Mapped["Subject"] = relationship(back_populates="topics")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Topic {self.name} subject={self.subject_id}>"
