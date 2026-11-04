"""Trace span: timed operation within a trace."""
import time
from typing import Any, Dict, Optional

from app.ai_core.tracing.context import TraceContext


class TraceSpan:
    def __init__(self, ctx: TraceContext, operation: str):
        self.ctx = ctx
        self.operation = operation
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status: Optional[str] = None
        self.error: Optional[str] = None
        self.attrs: dict[str, Any] = {}
        ctx.spans.append(self.to_dict())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.finish(status="error", error=str(exc_val))
        else:
            self.finish(status="ok")
        return False

    def set_attr(self, key: str, value: Any) -> None:
        self.attrs[key] = value

    def finish(self, status: str = "ok", error: Optional[str] = None) -> None:
        self.end_time = time.time()
        self.status = status
        self.error = error

    @property
    def latency_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "error": self.error,
            "attrs": self.attrs,
        }
