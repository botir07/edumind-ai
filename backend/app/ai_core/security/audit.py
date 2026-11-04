"""Security event audit logging for AI Core.

Logs security-relevant events without storing secrets or full private content.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID


class SecurityAuditor:
    """Records AI Core security events (caller persists to ai_security_events)."""

    def __init__(self):
        self.events: list[Dict[str, Any]] = []

    def record(
        self,
        event_type: str,
        severity: str,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        details: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a security event record. Never store secrets/PII in details."""
        # Sanitize details: strip potential tokens/keys
        safe_details = self._sanitize(details) if details else None
        event = {
            "event_type": event_type,
            "severity": severity,
            "organization_id": str(organization_id) if organization_id else None,
            "user_id": str(user_id) if user_id else None,
            "details": safe_details,
            "ip": ip,
            "user_agent": user_agent,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(event)
        return event

    @staticmethod
    def _sanitize(text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        import re

        # Redact anything resembling a bearer token or API key
        text = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", text, flags=re.IGNORECASE)
        text = re.sub(r"(api[_-]?key|secret|token)\s*[:=]\s*\S+", r"\1=[REDACTED]", text, flags=re.IGNORECASE)
        return text
