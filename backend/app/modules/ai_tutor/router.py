"""AI Tutor API routes (/api/v1/ai/tutor/*).

Integrates Phase 1 (students, orgs, RBAC) + Phase 2 AI Core (orchestration,
system prompt, RAG, MCP, security, cache, trace, model provider) with Phase 3
tutor sessions/messages. No parallel AI implementation.
"""
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.cache.service import CacheService
from app.ai_core.core.config import ai_settings
from app.ai_core.core.exceptions import AIProviderError, AISecurityError
from app.ai_core.mcp.server import MCPServer
from app.ai_core.models.provider import EmbeddingProvider, ModelProvider
from app.ai_core.models.phase3_tables import AITutorMessage
from app.ai_core.orchestration import AIRequestHandler
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
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models import Student

from .schemas import (
    TutorChatRequest,
    TutorChatResponse,
    TutorMessageOut,
    TutorSessionCreate,
    TutorSessionDetail,
    TutorSessionListItem,
    TutorSessionOut,
)
from .service import TutorService

router = APIRouter(prefix="/ai/tutor", tags=["ai_tutor"])

# ---------- Shared Phase 2 component instances ----------
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
# a real provider is registered via the Phase 2 registry.
_embedding_provider: Optional[EmbeddingProvider] = None
_retrieval: Optional[RetrievalPipeline] = None
_model_provider: Optional[ModelProvider] = None
_mcp_server: Optional[MCPServer] = None


def _build_service(db: AsyncSession, enforcer: AICoreEnforcer) -> TutorService:
    return TutorService(
        session=db,
        enforcer=enforcer,
        prompt_engine=prompt_engine,
        injection_guard=injection_guard,
        input_validator=input_validator,
        rate_limiter=rate_limiter,
        output_validator=output_validator,
        pii_scanner=pii_scanner,
        auditor=auditor,
        tracer=tracer,
        cache=cache_service,
        retrieval=_retrieval,
        embedding_provider=_embedding_provider,
        mcp_server=_mcp_server,
        model_provider=_model_provider,
    )


# ---------- Routes ----------

@router.post("/sessions", response_model=TutorSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: TutorSessionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
):
    """Create (or resume) a tutoring session for the current student."""
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can create tutor sessions")
    await enforcer.require_org_access(student.organization_id)

    service = _build_service(db, enforcer)
    session_obj = await service.get_or_create_session(
        student_id=student.id,
        mode=payload.mode,
        locale=payload.locale,
        subject_id=payload.subject_id,
        topic_id=payload.topic_id,
        title=payload.title,
    )
    return TutorSessionOut.model_validate(session_obj)


@router.get("/sessions", response_model=List[TutorSessionListItem])
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
    limit: int = Query(50, ge=1, le=200),
):
    """List the current student's tutoring sessions."""
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can list tutor sessions")
    await enforcer.require_org_access(student.organization_id)

    service = _build_service(db, enforcer)
    sessions = await service.list_sessions(student_id=student.id, limit=limit)
    items: List[TutorSessionListItem] = []
    for s in sessions:
        msg_result = await db.execute(
            select(func.count()).select_from(AITutorMessage).where(AITutorMessage.session_id == s.id)
        )
        msg_count = msg_result.scalar_one() or 0
        items.append(
            TutorSessionListItem(
                id=s.id,
                mode=s.mode,
                locale=s.locale,
                title=s.title,
                is_active=s.is_active,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=msg_count,
            )
        )
    return items


@router.get("/sessions/{session_id}", response_model=TutorSessionDetail)
async def get_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
):
    """Get a tutoring session with its messages (owner only)."""
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can view tutor sessions")

    service = _build_service(db, enforcer)
    session_obj = await service.get_session_with_messages(session_id=session_id, student_id=student.id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor session not found")

    return TutorSessionDetail.model_validate(session_obj)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
):
    """Delete a tutoring session (owner only)."""
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can delete tutor sessions")

    service = _build_service(db, enforcer)
    ok = await service.delete_session(session_id=session_id, student_id=student.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor session not found")
    return None


@router.post("/chat", response_model=TutorChatResponse)
async def chat(
    payload: TutorChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
):
    """Send a tutoring message and get an AI response through the Phase 2 pipeline."""
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can use the AI tutor")
    await enforcer.require_org_access(student.organization_id)

    service = _build_service(db, enforcer)
    try:
        result = await service.chat(
            student_id=student.id,
            message=payload.message,
            mode=payload.mode or "explain",
            locale=payload.locale or "uz",
            session_id=payload.session_id,
            subject_id=payload.subject_id,
            topic_id=payload.topic_id,
            use_rag=payload.use_rag,
            use_mcp=payload.use_mcp,
            use_cache=payload.use_cache,
            top_k=payload.top_k,
        )
    except AISecurityError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception:  # noqa: BLE001
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Tutor request failed")

    return TutorChatResponse(
        session_id=result["session_id"],
        message_id=result["message_id"],
        content=result["content"],
        citations=result.get("citations", []),
        sanitized=result.get("sanitized", False),
        provider=result.get("provider", "none"),
        model=result.get("model"),
        usage=result.get("usage", {}),
        trace_id=result.get("trace_id", ""),
    )
