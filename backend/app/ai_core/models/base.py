"""AI Core models base (SQLAlchemy placeholders)."""
# SQLAlchemy models for ai_* tables are defined via Alembic migration 0002_ai_core.
# Domain models (Pydantic) live in ai_core/api/schemas/.
# This module intentionally contains no ORM classes to avoid duplicating Phase 1 tables.
__all__ = []
