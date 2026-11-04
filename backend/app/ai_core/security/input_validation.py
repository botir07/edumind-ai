"""Input validation for AI Core requests."""
import os
import re
from typing import Any, Dict, Optional

from app.ai_core.core.config import ai_settings
from app.ai_core.core.exceptions import AIValidationError, AIRateLimitError

_MAX_PROMPT_LENGTH = ai_settings.prompt_max_length

# Dangerous patterns that should not appear in user prompts (structural, not just keywords)
_DANGEROUS_PATTERNS = [
    re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"data:text/html", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
]


class InputValidator:
    """Validates and sanitizes incoming AI requests."""

    @staticmethod
    def validate_text(text: Optional[str], field_name: str = "text") -> str:
        if text is None:
            return ""
        if len(text) > _MAX_PROMPT_LENGTH:
            raise AIValidationError(
                f"{field_name} too long",
                details={"field": field_name, "max_length": _MAX_PROMPT_LENGTH},
                status_code=400,
            )
        # null-byte strip
        cleaned = text.replace("\x00", "")
        # reject embedded script/html injection attempts
        for pat in _DANGEROUS_PATTERNS:
            if pat.search(cleaned):
                raise AIValidationError(
                    f"{field_name} contains disallowed content",
                    details={"field": field_name},
                    status_code=400,
                )
        return cleaned

    @staticmethod
    def validate_file(
        filename: Optional[str],
        content_type: Optional[str],
        size_bytes: Optional[int],
    ) -> Dict[str, Any]:
        """Validate an uploaded file. Returns sanitized metadata or raises."""
        errors: Dict[str, str] = {}
        if size_bytes is not None and size_bytes > ai_settings.max_document_size_mb * 1024 * 1024:
            errors["size"] = f"File exceeds {ai_settings.max_document_size_mb}MB"
        ext = ""
        if filename:
            ext = os.path.splitext(filename)[1].lower()
        if ext not in ai_settings.allowed_document_extensions:
            errors["extension"] = f"Extension {ext} not allowed"
        if content_type and content_type not in ai_settings.allowed_document_mimes:
            errors["mime"] = f"MIME {content_type} not allowed"
        if errors:
            raise AIValidationError("File validation failed", details=errors, status_code=400)
        return {"filename": filename, "extension": ext, "content_type": content_type, "size_bytes": size_bytes}

    @staticmethod
    def normalize_query(text: str) -> str:
        """Normalize a user query for embedding/retrieval."""
        return " ".join(text.split()).strip()


class RateLimiter:
    """Simple in-memory rate limiter (per key, per minute).

    Production should back this with Redis; this is a safe fallback.
    """

    def __init__(self, max_per_minute: Optional[int] = None):
        self.max_per_minute = max_per_minute or ai_settings.rate_limit_per_minute
        self._calls: Dict[str, list] = {}

    def check(self, key: str) -> None:
        import time

        now = time.time()
        window = now - 60
        timestamps = [t for t in self._calls.get(key, []) if t > window]
        if len(timestamps) >= self.max_per_minute:
            raise AIRateLimitError(
                "Rate limit exceeded",
                details={"key": key, "limit": self.max_per_minute},
            )
        timestamps.append(now)
        self._calls[key] = timestamps
