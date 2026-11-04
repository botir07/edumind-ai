"""PII detection and redaction helpers."""
import re
from typing import List


class PIIScanner:
    """Scans and redacts PII from text.

    Patterns are heuristic; intended for logging/safety, not authoritative.
    """

    def __init__(self):
        self._patterns = [
            ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
            ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
            ("card", re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")),
            ("phone", re.compile(r"\b\+?\d[\d\s-]{7,}\d\b")),
        ]

    def scan(self, text: str) -> dict:
        found = []
        for name, pat in self._patterns:
            for m in pat.finditer(text or ""):
                found.append({"type": name, "start": m.start(), "end": m.end()})
        return {"pii_found": bool(found), "matches": found}

    def redact(self, text: str) -> str:
        out = text or ""
        for _, pat in self._patterns:
            out = pat.sub("[REDACTED]", out)
        return out
