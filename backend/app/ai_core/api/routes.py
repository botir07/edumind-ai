"""AI Core API routes (/api/v1/ai/).

Mounted in app/api/v1/api.py. Reuses Phase 1 auth (get_current_user / require_role)
and database session. AI Core DB tables are defined by migration 0002_ai_core.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer, require_ai_org_access
from app.ai_core.cache.service import CacheService
from app.ai_core.core.config import ai_settings
from app.ai_core.core.exceptions import AICoreError
from app.ai_core.mcp.server import MCPServer
from app.ai_core.mcp.schemas import ToolCall
from app.ai_core.models.provider import EmbeddingProvider
from app.ai_core.orchestration import AIRequestHandler
from app.ai_core.rag.retrieval import RetrievalPipeline
from app.ai_core.security.audit import SecurityAuditor
from app.ai_core.security.input_validation import InputValidator, RateLimiter
from app.ai_core.security.output_validation import OutputValidator
from app.ai_core.security.pii import PIIScanner
from app.ai_core.system_prompt.engine import SystemPromptEngine
from app.ai_core.system_prompt.injection_guard import PromptInjectionGuard
from app.ai_core.tracing.exporter import TraceExporter
from app.api.v1.routers.auth import router as auth_router  # noqa: F401  (ensure auth loaded)
from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models import (  # noqa: F401
    AIDocument,
    AIPromptTemplate,
    AISecurityEvent,
    AITraceMetadata,
)

from .schemas import (  # noqa: E402
    ConfigStatusResponse,
    DocumentCreate,
    DocumentOut,
    HealthResponse,
    PromptTemplateCreate,
    PromptTemplateOut,
    RagSearchRequest,
    RagSearchResponse,
    SecurityEventOut,
    ToolExecuteRequest,
    ToolExecuteResponse,
    TraceOut,
)

router = APIRouter(prefix="/ai", tags=["ai_core"])

# ---------------------------------------------------------------------------
# Component instances (shared across requests; provider/test doubles unless configured)
# ---------------------------------------------------------------------------
prompt_engine = SystemPromptEngine()
injection_guard = PromptInjectionGuard()
input_validator = InputValidator()
rate_limiter = RateLimiter()
output_validator = OutputValidator()
pii_scanner = PIIScanner()
auditor = SecurityAuditor()
tracer = TraceExporter()
cache_service = CacheService()

# Embedding provider / vector store / retrieval pipeline use test doubles unless
# a real provider is registered via the registry.
_embedding_provider: Optional[EmbeddingProvider] = None
_retrieval: Optional[RetrievalPipeline] = None
_model_provider = None  # set when a provider is authorized
_mcp_server: Optional[MCPServer] = None


def _build_handler(enforcer) -> AIRequestHandler:
    return AIRequestHandler(
        enforcer=enforcer,
        prompt_engine=prompt_engine,
        injection_guard=injection_guard,
        input_validator=input_validator,
        rate_limiter=rate_limiter,
        retrieval=_retrieval,
        mcp_server=_mcp_server,
        cache=cache_service,
        model_provider=_model_provider,
        embedding_provider=_embedding_provider,
        output_validator=output_validator,
        pii_scanner=pii_scanner,
        auditor=auditor,
        tracer=tracer,
    )


# ---------------------------------------------------------------------------
# Health & config
# ---------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def ai_health():
    components = {
        "system_prompt": "ok",
        "access_control": "ok",
        "security": "ok",
        "rag": "ok" if _retrieval else "not_configured",
        "mcp": "ok" if _mcp_server else "not_configured",
        "cache": "ok",
        "trace": "ok",
        "model_provider": "ok" if (_model_provider and _model_provider.is_enabled) else "not_configured",
    }
    return HealthResponse(status="ok", components=components)


@router.get("/config/status", response_model=ConfigStatusResponse, status_code=status.HTTP_200_OK)
async def ai_config_status(current_user=Depends(get_current_user)):
    return ConfigStatusResponse(
        ai_core_enabled=ai_settings.ai_core_enabled,
        rag_enabled=ai_settings.rag_enabled,
        mcp_enabled=ai_settings.mcp_enabled,
        cache_enabled=ai_settings.cache_enabled,
        trace_enabled=ai_settings.trace_enabled,
        providers=list(ai_settings.enabled_providers),
        default_llm_provider=ai_settings.default_llm_provider,
        default_embedding_provider=ai_settings.default_embedding_provider,
    )


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
@router.get("/prompts", response_model=List[PromptTemplateOut])
async def list_prompts(
    role: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AIPromptTemplate).where(AIPromptTemplate.is_active == True)  # noqa: E712
    if role:
        query = query.where(AIPromptTemplate.role == role)
    if language:
        query = query.where(AIPromptTemplate.language == language)
    # org scope: return platform-wide + user's org templates
    memberships = await get_active_memberships(current_user, db)
    org_ids = [str(m.organization_id) for m in memberships]
    if org_ids:
        query = query.where(
            (AIPromptTemplate.organization_id.is_(None)) | (AIPromptTemplate.organization_id.in_(org_ids))
        )
    else:
        query = query.where(AIPromptTemplate.organization_id.is_(None))
    result = await db.execute(query)
    return [PromptTemplateOut.model_validate(r) for r in result.scalars().all()]


@router.post("/prompts", response_model=PromptTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    payload: PromptTemplateCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    # org access
    enforcer = await get_ai_enforcer(current_user, db)
    await enforcer.require_org_access(payload.organization_id) if payload.organization_id else None

    obj = AIPromptTemplate(
        organization_id=payload.organization_id,
        name=payload.name,
        role=payload.role,
        language=payload.language,
        content=payload.content,
        is_active=payload.is_active,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    # audit version
    auditor.record(
        "prompt_create", "low",
        organization_id=payload.organization_id,
        user_id=current_user["id"],
        details=f"prompt {payload.name} v1",
    )
    return PromptTemplateOut.model_validate(obj)


@router.patch("/prompts/{prompt_id}", response_model=PromptTemplateOut)
async def update_prompt(
    prompt_id: UUID,
    payload: PromptTemplateCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(AIPromptTemplate, prompt_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    enforcer = await get_ai_enforcer(current_user, db)
    await enforcer.require_org_access(obj.organization_id) if obj.organization_id else None
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    obj.version = (obj.version or 0) + 1
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    auditor.record(
        "prompt_update", "medium",
        organization_id=obj.organization_id,
        user_id=current_user["id"],
        details=f"prompt {obj.name} v{obj.version}",
    )
    return PromptTemplateOut.model_validate(obj)


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: UUID,
    current_user=Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(AIPromptTemplate, prompt_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    await db.delete(obj)
    await db.flush()
    return None


# ---------------------------------------------------------------------------
# Documents (RAG)
# ---------------------------------------------------------------------------
@router.get("/documents", response_model=List[DocumentOut])
async def list_documents(
    organization_id: Optional[UUID] = Query(None),
    subject: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enforcer = await get_ai_enforcer(current_user, db)
    org_id = organization_id
    if org_id is None:
        memberships = await get_active_memberships(current_user, db)
        org_ids = [m.organization_id for m in memberships]
        if not org_ids:
            return []
        org_id = org_ids[0]
    await enforcer.require_org_access(org_id)
    query = select(AIDocument).where(
        AIDocument.organization_id == org_id,
        AIDocument.deleted_at.is_(None),
    )
    if subject:
        query = query.where(AIDocument.subject == subject)
    result = await db.execute(query)
    return [DocumentOut.model_validate(r) for r in result.scalars().all()]


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    enforcer = await get_ai_enforcer(current_user, db)
    await enforcer.require_org_access(payload.organization_id)
    obj = AIDocument(
        organization_id=payload.organization_id,
        title=payload.title,
        subject=payload.subject,
        language=payload.language,
        source=payload.source,
        uploader_id=current_user["id"],
        access_level=payload.access_level,
        checksum=payload.checksum,
        file_path=payload.file_path,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        processing_status=payload.processing_status,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    auditor.record(
        "document_ingest", "low",
        organization_id=payload.organization_id,
        user_id=current_user["id"],
        details=f"document {payload.title}",
    )
    return DocumentOut.model_validate(obj)


@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(AIDocument, document_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    enforcer = await get_ai_enforcer(current_user, db)
    await enforcer.require_org_access(obj.organization_id)
    return DocumentOut.model_validate(obj)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(AIDocument, document_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    enforcer = await get_ai_enforcer(current_user, db)
    await enforcer.require_org_access(obj.organization_id)
    obj.deleted_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    db.add(obj)
    await db.flush()
    return None


@router.post("/documents/{document_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_document(
    document_id: UUID,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(AIDocument, document_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    enforcer = await get_ai_enforcer(current_user, db)
    await enforcer.require_org_access(obj.organization_id)
    obj.processing_status = "pending"
    db.add(obj)
    await db.flush()
    auditor.record(
        "document_reindex", "low",
        organization_id=obj.organization_id,
        user_id=current_user["id"],
        details=f"reindex document {obj.title}",
    )
    return {"document_id": str(document_id), "processing_status": "pending"}


# ---------------------------------------------------------------------------
# RAG search
# ---------------------------------------------------------------------------
@router.post("/rag/search", response_model=RagSearchResponse)
async def rag_search(
    payload: RagSearchRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enforcer = await get_ai_enforcer(current_user, db)
    memberships = await get_active_memberships(current_user, db)
    org_ids = [m.organization_id for m in memberships]
    if not org_ids:
        return RagSearchResponse(chunks=[], citations=[], total_returned=0, query_hash="")

    # Use the first active org as scope
    org_id = org_ids[0]
    await enforcer.require_org_access(org_id)

    if not ai_settings.rag_enabled or not _retrieval:
        return RagSearchResponse(chunks=[], citations=[], total_returned=0, query_hash="")

    import hashlib
    query_hash = hashlib.sha256(payload.query.encode()).hexdigest()[:16]
    result = await _retrieval.retrieve(
        query=payload.query,
        top_k=payload.top_k,
        subject=payload.subject,
        language=payload.language,
    )
    chunks = [
        RagSearchResult(
            document_id=UUID(c["document_id"]),
            content=c.get("content", ""),
            score=c.get("score", 0.0),
            source_title=c.get("source_title"),
            subject=c.get("subject"),
            page=c.get("page"),
            section=c.get("section"),
        )
        for c in result.get("chunks", [])
    ]
    auditor.record(
        "rag_search", "low",
        organization_id=org_id,
        user_id=current_user["id"],
        details=f"query_hash={query_hash} results={result.get('total_returned', 0)}",
    )
    return RagSearchResponse(
        chunks=chunks,
        citations=result.get("citations", []),
        total_returned=result.get("total_returned", 0),
        query_hash=query_hash,
    )


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------
@router.get("/tools", response_model=List[Dict[str, Any]])
async def list_tools(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enforcer = await get_ai_enforcer(current_user, db)
    roles = await enforcer.user_roles()
    role = roles[0] if roles else None
    server = MCPServer(enforcer)
    tools = await server.list_tools(role=role)
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "tool_type": t.tool_type,
            "is_read_only": t.is_read_only,
            "required_role": t.required_role,
        }
        for t in tools
    ]


@router.post("/tools/{tool_name}/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    tool_name: str,
    payload: ToolExecuteRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enforcer = await get_ai_enforcer(current_user, db)
    server = MCPServer(enforcer)
    call = ToolCall(
        name=tool_name,
        arguments=payload.arguments,
        user_id=str(current_user["id"]),
        organization_id="",  # server-resolved, ignored
    )
    result = await server.call_tool(call)
    # audit execution
    memberships = await get_active_memberships(current_user, db)
    org_id = str(memberships[0].organization_id) if memberships else None
    auditor.record(
        "mcp_execute", "low",
        organization_id=UUID(org_id) if org_id else None,
        user_id=current_user["id"],
        details=f"tool {tool_name} success={result.success}",
    )
    return ToolExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        error_code=result.error_code,
    )


# ---------------------------------------------------------------------------
# Traces
# ---------------------------------------------------------------------------
@router.get("/traces", response_model=List[TraceOut])
async def list_traces(
    organization_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enforcer = await get_ai_enforcer(current_user, db)
    org_id = organization_id
    if org_id is None:
        memberships = await get_active_memberships(current_user, db)
        org_ids = [m.organization_id for m in memberships]
        if not org_ids:
            return []
        org_id = org_ids[0]
    await enforcer.require_org_access(org_id)
    query = select(AITraceMetadata).where(AITraceMetadata.organization_id == org_id).order_by(
        AITraceMetadata.created_at.desc()
    ).limit(100)
    result = await db.execute(query)
    return [TraceOut.model_validate(r) for r in result.scalars().all()]


@router.get("/traces/{trace_id}", response_model=TraceOut)
async def get_trace(
    trace_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AITraceMetadata).where(AITraceMetadata.trace_id == trace_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    enforcer = await get_ai_enforcer(current_user, db)
    await enforcer.require_org_access(obj.organization_id)
    return TraceOut.model_validate(obj)


# ---------------------------------------------------------------------------
# Security events
# ---------------------------------------------------------------------------
@router.get("/security/events", response_model=List[SecurityEventOut])
async def list_security_events(
    organization_id: Optional[UUID] = Query(None),
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    enforcer = await get_ai_enforcer(current_user, db)
    org_id = organization_id
    if org_id is None:
        memberships = await get_active_memberships(current_user, db)
        org_ids = [m.organization_id for m in memberships]
        if not org_ids:
            return []
        org_id = org_ids[0]
    await enforcer.require_org_access(org_id)
    query = select(AISecurityEvent).where(AISecurityEvent.organization_id == org_id).order_by(
        AISecurityEvent.created_at.desc()
    ).limit(100)
    result = await db.execute(query)
    return [SecurityEventOut.model_validate(r) for r in result.scalars().all()]
