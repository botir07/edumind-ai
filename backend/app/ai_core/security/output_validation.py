"""Output validation for AI Core responses."""
import re
from typing import Any, Dict, List, Optional

from app.ai_core.core.exceptions import AICoreError


class OutputValidator:
    """Validates AI responses before returning to the client.

    Checks: structure, PII leakage, internal prompt echo, citation validity.
    """

    # PII-ish patterns (simple heuristics; production may use a dedicated PII lib)
    _PII_PATTERNS = [
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN-like
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),  # email
        re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),  # card-like
    ]

    # Internal markers that must never be echoed back
    _INTERNAL_MARKERS = ["[SYSTEM]", "[ROLE POLICY]", "[SAFETY POLICY]", "[CONTEXT]"]

    def validate(self, response: str, citations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Validate and sanitize a model response.

        Returns {content, sanitized, pii_found, internal_echo, citations_ok}.
        Never raises on content issues — returns flags so the caller can decide.
        """
        content = response or ""
        pii_found = [p.pattern for p in self._PII_PATTERNS if p.search(content)]
        internal_echo = [m for m in self._INTERNAL_MARKERS if m in content]

        # Redact PII matches
        sanitized = content
        for pat in self._PII_PATTERNS:
            sanitized = pat.sub("[REDACTED]", sanitized)

        # Strip internal markers
        for m in self._INTERNAL_MARKERS:
            sanitized = sanitized.replace(m, "")

        citations_ok = True
        if citations:
            for c in citations:
                if not c.get("document_id") or not c.get("title"):
                    citations_ok = False

        return {
            "content": sanitized,
            "sanitized": sanitized != content,
            "pii_found": bool(pii_found),
            "internal_echo": bool(internal_echo),
            "citations_ok": citations_ok,
        }


class PIIScanner:
    """Scans text for personally identifiable information."""

    def __init__(self):
        self.validator = OutputValidator()

    def scan(self, text: str) -> Dict[str, Any]:
        result = self.validator.validate(text)
        return {
            "pii_found": result["pii_found"],
            "has_pii": result["pii_found"],
            "sanitized": result["sanitized"],
            "content": result["content"],
        }

    def redact(self, text: str) -> str:
        return self.validator.validate(text)["content"]
