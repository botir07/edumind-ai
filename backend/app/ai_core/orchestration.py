"""AI Core orchestration: the unified AI request pipeline.

Logical sequence:
  Incoming Request
    -> Authentication (reuses Phase 1 get_current_user)
    -> Access Control (AICoreEnforcer)
    -> Input Security (InputValidator, RateLimiter, PromptInjectionGuard)
    -> System Prompt (SystemPromptEngine)
    -> RAG Retrieval (RetrievalPipeline) [optional]
    -> MCP Tool Registry [optional]
    -> Cache (CacheService) [optional]
    -> Model Provider Adapter (ModelProvider) [test double unless authorized]
    -> Output Security (OutputValidator, PIIScanner)
    -> Response + Citations
    -> Trace + Metrics

Each component has a clear contract. Errors in one component do not leak
internal data from another.
"""
import time
from typing import Any, Dict, Optional
from uuid import UUID

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.cache.service import CacheService
from app.ai_core.core.exceptions import AICoreError, AISecurityError, AIProviderError
from app.ai_core.mcp.server import MCPServer
from app.ai_core.models.provider import EmbeddingProvider, ModelProvider, ModelRequest, ModelResponse
from app.ai_core.rag.embeddings import EmbeddingProvider as RAGEmbeddingProvider
from app.ai_core.rag.retrieval import RetrievalPipeline
from app.ai_core.security.audit import SecurityAuditor
from app.ai_core.security.input_validation import InputValidator, RateLimiter
from app.ai_core.security.output_validation import OutputValidator
from app.ai_core.security.pii import PIIScanner
from app.ai_core.system_prompt.engine import SystemPromptEngine
from app.ai_core.system_prompt.injection_guard import PromptInjectionGuard
from app.ai_core.tracing.context import TraceContext
from app.ai_core.tracing.exporter import TraceExporter


class AIRequestHandler:
    """Orchestrates a single AI request through all seven components."""

    def __init__(
        self,
        *,
        enforcer: AICoreEnforcer,
        prompt_engine: SystemPromptEngine,
        injection_guard: PromptInjectionGuard,
        input_validator: InputValidator,
        rate_limiter: RateLimiter,
        retrieval: Optional[RetrievalPipeline] = None,
        mcp_server: Optional[MCPServer] = None,
        cache: Optional[CacheService] = None,
        model_provider: Optional[ModelProvider] = None,
        embedding_provider: Optional[RAGEmbeddingProvider] = None,
        output_validator: OutputValidator,
        pii_scanner: PIIScanner,
        auditor: SecurityAuditor,
        tracer: TraceExporter,
    ):
        self.enforcer = enforcer
        self.prompt_engine = prompt_engine
        self.injection_guard = injection_guard
        self.input_validator = input_validator
        self.rate_limiter = rate_limiter
        self.retrieval = retrieval
        self.mcp_server = mcp_server
        self.cache = cache
        self.model_provider = model_provider
        self.embedding_provider = embedding_provider
        self.output_validator = output_validator
        self.pii_scanner = pii_scanner
        self.auditor = auditor
        self.tracer = tracer

    async def handle(
        self,
        *,
        user_message: str,
        role: str,
        locale: str = "uz",
        organization_id: Optional[UUID] = None,
        use_rag: bool = False,
        use_mcp: bool = False,
        use_cache: bool = False,
        top_k: int = 10,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        ctx = TraceContext(
            trace_id=None,
            organization_id=str(organization_id) if organization_id else None,
            user_id=str(getattr(self.enforcer, "user_id", "")),
            operation="ai_request",
        )

        def span(name):
            return ctx.child_span(name)

        # 1. Authentication already done by enforcer (built from get_current_user)
        with span("authentication") as s:
            s.finish(status="ok")

        # 2. Access control
        with span("access_control") as s:
            await self.enforcer.require_org_access(organization_id) if organization_id else None
            max_k = await self.enforcer.max_top_k()
            top_k = min(top_k, max_k)
            s.finish(status="ok")

        # 3. Input security
        with span("input_security") as s:
            safe_message = self.input_validator.validate_text(user_message, "user_message")
            self.rate_limiter.check(f"ai:{self.enforcer.user_id}")
            injection = self.injection_guard.scan(safe_message)
            if injection["risk_level"] == "high":
                self.auditor.record(
                    "prompt_injection", "high",
                    organization_id=organization_id,
                    user_id=self.enforcer.user_id,
                    details="blocked high-risk user message",
                )
                raise AISecurityError("Message rejected by input security")
            s.finish(status="ok")

        # 4. System prompt
        with span("system_prompt") as s:
            system_prompt = await self.prompt_engine.build_system_prompt(
                role=role, locale=locale, organization_id=organization_id,
                context_injection={"locale": locale},
            )
            s.finish(status="ok")

        # 5. RAG retrieval (optional)
        citations = []
        rag_context = ""
        with span("rag_retrieval") as s:
            if use_rag and self.retrieval and self.embedding_provider:
                rag_result = await self.retrieval.retrieve(
                    query=safe_message, top_k=top_k, subject=subject, language=locale,
                )
                rag_context = "\n".join(c.get("content", "") for c in rag_result.get("chunks", []))
                citations = rag_result.get("citations", [])
                s.set_attr("chunks_returned", rag_result.get("total_returned", 0))
            s.finish(status="ok")

        # 6. MCP tools (optional)
        mcp_data = {}
        with span("mcp_tools") as s:
            if use_mcp and self.mcp_server:
                # Placeholder: MCP invoked by provider, not directly here.
                s.set_attr("tools_available", True)
            s.finish(status="ok")

        # 7. Cache (optional)
        cache_key = f"{role}:{locale}:{hashlib_sha256(safe_message)[:16]}"
        cached = None
        with span("cache") as s:
            if use_cache and self.cache and organization_id:
                cached = await self.cache.get(str(organization_id), "ai_response", cache_key)
                s.set_attr("cache_hit", cached is not None)
            s.finish(status="ok")

        # 8. Model provider (optional; test double unless authorized)
        model_response: Optional[ModelResponse] = None
        with span("model_provider") as s:
            if self.model_provider and self.model_provider.is_enabled:
                messages = [{"role": "system", "content": system_prompt}]
                if rag_context:
                    messages.append({"role": "user", "content": f"[Retrieved context]\n{rag_context}\n\n[Question]\n{safe_message}"})
                else:
                    messages.append({"role": "user", "content": safe_message})
                req = ModelRequest(
                    messages=messages,
                    organization_id=organization_id,
                    user_id=self.enforcer.user_id,
                )
                model_response = await self.model_provider.generate(req)
                s.set_attr("provider", self.model_provider.name)
            else:
                model_response = ModelResponse(
                    content="[AI provider not configured]",
                    provider="none",
                )
            s.finish(status="ok")

        # 9. Output security
        with span("output_security") as s:
            validated = self.output_validator.validate(model_response.content, citations)
            final_content = validated["content"]
            if validated["pii_found"] or validated["internal_echo"]:
                self.auditor.record(
                    "output_security", "medium",
                    organization_id=organization_id,
                    user_id=self.enforcer.user_id,
                    details="pii or internal echo redacted",
                )
            s.finish(status="ok")

        # 10. Trace + metrics
        with span("trace") as s:
            self.tracer.export_trace(ctx)
            s.finish(status="ok")

        # Cache the response (safe, non-personal only if appropriate)
        if use_cache and self.cache and organization_id and not validated["pii_found"]:
            await self.cache.set(str(organization_id), "ai_response", cache_key, final_content, ttl_seconds=300)

        return {
            "trace_id": ctx.trace_id,
            "content": final_content,
            "citations": citations,
            "sanitized": validated["sanitized"],
            "provider": model_response.provider if model_response else "none",
            "model": model_response.model if model_response else None,
            "usage": model_response.usage if model_response else {},
        }


def hashlib_sha256(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class OrchestrationPipeline:
    """Factory-friendly wrapper around AIRequestHandler."""

    def __init__(self, handler: AIRequestHandler):
        self.handler = handler

    async def run(self, **kwargs) -> Dict[str, Any]:
        return await self.handler.handle(**kwargs)
