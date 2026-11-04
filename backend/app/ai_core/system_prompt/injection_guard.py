"""System Prompt Engine: prompt injection defense.

Validates that user-supplied content and retrieved RAG documents cannot alter
the composed system prompt. Implements multi-layer defense without relying
solely on keyword detection.
"""
import re
from typing import Any, Dict, List


class PromptInjectionGuard:
    """Defense against prompt injection via user messages and RAG content."""

    # Patterns that attempt to redefine system behavior (not exhaustive; used as
    # one layer of defense alongside structural separation).
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+(instructions|rules|prompt)",
        r"you\s+are\s+now\s+(a|an)",
        r"disregard\s+(the\s+)?(system|safety)",
        r"system\s*:\s*",
        r"\[SYSTEM\]",
        r"new\s+instructions\s*:",
        r"override\s+(safety|security|policy)",
        r"jailbreak",
        r"DAN\s*(:| )",
    ]

    _compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    def scan(self, text: str) -> Dict[str, Any]:
        """Scan text for injection patterns. Returns {risk_level, matches}."""
        matches = [p.pattern for p in self._compiled if p.search(text or "")]
        risk = "high" if matches else "low"
        return {"risk_level": risk, "matches": matches}

    def is_safe(self, text: str) -> bool:
        return self.scan(text)["risk_level"] == "low"

    def sanitize_for_user_message(self, text: str) -> str:
        """Prepare retrieved document content for safe insertion as user context.

        Strips potential system-prompt delimiters so document content cannot
        masquerade as system instructions.
        """
        cleaned = text or ""
        cleaned = cleaned.replace("[SYSTEM]", "[CONTENT]")
        cleaned = cleaned.replace("system:", "label:")
        return cleaned
