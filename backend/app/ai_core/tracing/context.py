"""Trace context: every AI request gets a trace_id propagated across components."""
import uuid
from typing import Any, Dict, Optional


class TraceContext:
    """Holds the current trace context for an AI request."""

    def __init__(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        self.trace_id = trace_id or uuid.uuid4().hex
        self.span_id = span_id or uuid.uuid4().hex
        self.organization_id = organization_id
        self.user_id = user_id
        self.operation = operation
        self.spans: list[dict] = []

    def child_span(self, operation: str):
        # lazy import to avoid circular import with spans.py
        from app.ai_core.tracing.spans import TraceSpan

        return TraceSpan(self, operation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "operation": self.operation,
            "spans": self.spans,
        }
