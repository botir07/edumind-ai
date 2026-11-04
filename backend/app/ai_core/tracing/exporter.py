"""Trace exporter: emits structured logs (OpenTelemetry-compatible shape).

Does not log secrets, tokens, or full private content.
"""
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("edumind.ai.trace")


class TraceExporter:
    def export_trace(self, ctx) -> None:
        payload = {
            "trace_id": ctx.trace_id,
            "span_id": ctx.span_id,
            "organization_id": ctx.organization_id,
            "user_id": ctx.user_id,
            "operation": ctx.operation,
            "spans": ctx.spans,
        }
        logger.info("AI_TRACE %s", json.dumps(payload))

    def export_event(self, event: str, ctx, **attrs) -> None:
        payload = {
            "event": event,
            "trace_id": ctx.trace_id,
            "organization_id": ctx.organization_id,
            "attrs": attrs,
        }
        logger.info("AI_TRACE_EVENT %s", json.dumps(payload))
