"""Trace tests (run with pytest)."""
import pytest

from app.ai_core.tracing.context import TraceContext
from app.ai_core.tracing.spans import TraceSpan
from app.ai_core.tracing.exporter import TraceExporter


def test_trace_context_creation():
    ctx = TraceContext(organization_id="org1", user_id="u1", operation="rag_query")
    assert ctx.trace_id
    assert ctx.span_id
    assert ctx.organization_id == "org1"
    assert ctx.operation == "rag_query"


def test_child_span():
    ctx = TraceContext(organization_id="org1", operation="rag_query")
    span = ctx.child_span("vector_search")
    span.set_attr("top_k", 10)
    span.finish(status="ok")
    assert span.latency_ms is not None
    assert span.status == "ok"
    assert len(ctx.spans) == 1
    assert ctx.spans[0]["operation"] == "vector_search"


def test_exporter_no_secrets():
    exporter = TraceExporter()
    ctx = TraceContext(organization_id="org1", user_id="u1", operation="rag_query")
    span = ctx.child_span("provider_call")
    span.finish(status="ok")
    # capture log output
    import io
    import logging
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("edumind.ai.trace")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    exporter.export_trace(ctx)
    out = stream.getvalue()
    logger.removeHandler(handler)
    assert "org1" in out
    assert ctx.trace_id in out
    # no secret keywords
    assert "secret" not in out.lower()
    assert "password" not in out.lower()
