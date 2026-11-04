"""Prompt versioning helpers (in-memory + DB persistence contract)."""
from typing import Any, Dict, List, Optional
from uuid import UUID


class PromptVersioning:
    """Tracks prompt template versions. Persistence layer is the caller (DB
    ai_prompt_versions table); this class holds the versioning logic."""

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def next_version(self, template_name: str) -> int:
        existing = [v for v in self._history if v["template_name"] == template_name]
        return (max((v["version"] for v in existing), default=0) + 1)

    def record(
        self,
        template_name: str,
        content: str,
        changed_by: Optional[UUID] = None,
        change_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        version = self.next_version(template_name)
        record = {
            "template_name": template_name,
            "version": version,
            "content": content,
            "changed_by": str(changed_by) if changed_by else None,
            "change_reason": change_reason,
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
        self._history.append(record)
        return record

    def history(self, template_name: str) -> List[Dict[str, Any]]:
        return [v for v in self._history if v["template_name"] == template_name]

    def latest(self, template_name: str) -> Optional[Dict[str, Any]]:
        hist = self.history(template_name)
        return hist[-1] if hist else None
