"""AI Tutor service.

Orchestrates tutoring through Phase 2 AI Core components (System Prompt, RAG,
MCP, Access Control, Security, Cache, Trace, Model Provider). No parallel AI
implementation; all AI capabilities flow through Phase 2 contracts.

No real Model Provider is connected. When none is configured, the tutor returns
a clear "[AI provider not configured]" message — never a fake answer.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.cache.service import CacheService
from app.ai_core.core.config import ai_settings
from app.ai_core.core.exceptions import AISecurityError, AIProviderError
from app.ai_core.mcp.server import MCPServer
from app.ai_core.models.provider import EmbeddingProvider, ModelProvider, ModelRequest, ModelResponse
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
from app.ai_core.models.phase3_tables import (
    AITutorSession,
    AITutorMessage,
    AIStudentKnowledgeState,
    AILearningAttempt,
)
from app.models.student import Student


def _hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TutorService:
    """Service for AI tutoring sessions and messages."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        enforcer: AICoreEnforcer,
        prompt_engine: SystemPromptEngine,
        injection_guard: PromptInjectionGuard,
        input_validator: InputValidator,
        rate_limiter: RateLimiter,
        output_validator: OutputValidator,
        pii_scanner: PIIScanner,
        auditor: SecurityAuditor,
        tracer: TraceExporter,
        cache: Optional[CacheService] = None,
        retrieval: Optional[RetrievalPipeline] = None,
        embedding_provider: Optional[RAGEmbeddingProvider] = None,
        mcp_server: Optional[MCPServer] = None,
        model_provider: Optional[ModelProvider] = None,
    ):
        self.session = session
        self.enforcer = enforcer
        self.prompt_engine = prompt_engine
        self.injection_guard = injection_guard
        self.input_validator = input_validator
        self.rate_limiter = rate_limiter
        self.output_validator = output_validator
        self.pii_scanner = pii_scanner
        self.auditor = auditor
        self.tracer = tracer
        self.cache = cache
        self.retrieval = retrieval
        self.embedding_provider = embedding_provider
        self.mcp_server = mcp_server
        self.model_provider = model_provider

    # ---------- session management ----------

    async def get_or_create_session(
        self,
        student_id: UUID,
        mode: str = "explain",
        locale: str = "uz",
        subject_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        title: Optional[str] = None,
    ) -> AITutorSession:
        """Get the student's latest active session or create a new one.

        Enforces that the student belongs to the session's organization.
        """
        # Verify student exists and get their org
        student = await self.session.get(Student, student_id)
        if not student or student.status != "active":
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Student not found")

        org_id = student.organization_id
        await self.enforcer.require_org_access(org_id)

        # Look for latest active session for this student/org
        result = await self.session.execute(
            select(AITutorSession).where(
                AITutorSession.student_id == student_id,
                AITutorSession.organization_id == org_id,
                AITutorSession.is_active == True,  # noqa: E712
            ).order_by(AITutorSession.updated_at.desc()).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Update locale/mode/subject/topic if provided
            if locale:
                existing.locale = locale
            if mode:
                existing.mode = mode
            if subject_id is not None:
                existing.subject_id = subject_id
            if topic_id is not None:
                existing.topic_id = topic_id
            if title is not None:
                existing.title = title
            self.session.add(existing)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        # Create new session
        session_obj = AITutorSession(
            student_id=student_id,
            organization_id=org_id,
            mode=mode,
            locale=locale,
            subject_id=subject_id,
            topic_id=topic_id,
            title=title,
            is_active=True,
        )
        self.session.add(session_obj)
        await self.session.flush()
        await self.session.refresh(session_obj)
        return session_obj

    async def end_session(self, session_id: UUID, student_id: UUID) -> AITutorSession:
        """End (deactivate) a tutoring session. Student may only end their own."""
        result = await self.session.execute(
            select(AITutorSession).where(
                AITutorSession.id == session_id,
                AITutorSession.student_id == student_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Tutor session not found")
        await self.enforcer.require_org_access(obj.organization_id)
        obj.is_active = False
        obj.ended_at = datetime.now(timezone.utc)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def list_sessions(self, student_id: UUID, limit: int = 50) -> List[AITutorSession]:
        """List a student's tutoring sessions."""
        result = await self.session.execute(
            select(AITutorSession).where(
                AITutorSession.student_id == student_id,
            ).order_by(AITutorSession.updated_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def get_session_with_messages(self, session_id: UUID, student_id: UUID) -> Optional[AITutorSession]:
        """Get a session with its messages. Student may only access their own."""
        result = await self.session.execute(
            select(AITutorSession).where(
                AITutorSession.id == session_id,
                AITutorSession.student_id == student_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        await self.enforcer.require_org_access(obj.organization_id)
        # Load messages
        msg_result = await self.session.execute(
            select(AITutorMessage).where(
                AITutorMessage.session_id == session_id
            ).order_by(AITutorMessage.created_at.asc())
        )
        obj.messages = msg_result.scalars().all()
        return obj

    async def delete_session(self, session_id: UUID, student_id: UUID) -> bool:
        """Delete a tutoring session and its messages. Student may only delete their own."""
        result = await self.session.execute(
            select(AITutorSession).where(
                AITutorSession.id == session_id,
                AITutorSession.student_id == student_id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await self.enforcer.require_org_access(obj.organization_id)
        await self.session.delete(obj)
        await self.session.flush()
        return True

    # ---------- tutoring turn ----------

    async def chat(
        self,
        *,
        student_id: UUID,
        message: str,
        mode: str = "explain",
        locale: str = "uz",
        session_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        use_rag: bool = False,
        use_mcp: bool = False,
        use_cache: bool = False,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """Handle a single tutoring turn through the full Phase 2 pipeline."""
        # Get/create session + enforce org access
        tutor_session = await self.get_or_create_session(
            student_id=student_id,
            mode=mode,
            locale=locale,
            subject_id=subject_id,
            topic_id=topic_id,
        )
        org_id = tutor_session.organization_id
        session_id = tutor_session.id

        # Build the orchestration handler
        handler = AIRequestHandler(
            enforcer=self.enforcer,
            prompt_engine=self.prompt_engine,
            injection_guard=self.injection_guard,
            input_validator=self.input_validator,
            rate_limiter=self.rate_limiter,
            retrieval=self.retrieval,
            mcp_server=self.mcp_server,
            cache=self.cache,
            model_provider=self.model_provider,
            embedding_provider=self.embedding_provider,
            output_validator=self.output_validator,
            pii_scanner=self.pii_scanner,
            auditor=self.auditor,
            tracer=self.tracer,
        )

        # Run the AI request through the pipeline
        result = await handler.handle(
            user_message=message,
            role="STUDENT",
            locale=locale,
            organization_id=org_id,
            use_rag=use_rag,
            use_mcp=use_mcp,
            use_cache=use_cache,
            top_k=top_k,
            subject=str(subject_id) if subject_id else None,
        )

        # Persist user message
        user_msg = AITutorMessage(
            session_id=session_id,
            role="user",
            content=message,
            mode=mode,
            trace_id=result.get("trace_id"),
            citations=None,
            provider="user",
            usage=None,
            latency_ms=None,
        )
        self.session.add(user_msg)
        await self.session.flush()

        # Persist assistant message
        assistant_msg = AITutorMessage(
            session_id=session_id,
            role="assistant",
            content=result.get("content", ""),
            mode=mode,
            trace_id=result.get("trace_id"),
            citations=json.dumps(result.get("citations", [])) if result.get("citations") else None,
            provider=result.get("provider"),
            usage=json.dumps(result.get("usage", {})) if result.get("usage") else None,
            latency_ms=None,
        )
        self.session.add(assistant_msg)
        await self.session.flush()
        await self.session.refresh(assistant_msg)

        # Record a learning attempt if the mode is practice/quiz and we can infer correctness
        # (The tutor response may include correctness; here we record the attempt generically)
        # Note: correctness is determined when the student submits an answer (see error analysis).

        await self.session.commit()

        return {
            "session_id": session_id,
            "message_id": assistant_msg.id,
            "content": result.get("content", ""),
            "citations": result.get("citations", []),
            "sanitized": result.get("sanitized", False),
            "provider": result.get("provider", "none"),
            "model": result.get("model"),
            "usage": result.get("usage", {}),
            "trace_id": result.get("trace_id", ""),
        }

    # ---------- knowledge state helpers (used by knowledge map / adaptive learning) ----------

    async def record_learning_attempt(
        self,
        *,
        student_id: UUID,
        subject_id: Optional[UUID],
        topic_id: Optional[UUID],
        skill_id: Optional[UUID],
        session_id: Optional[UUID],
        attempt_type: str,
        question: str,
        student_answer: Optional[str],
        correct_answer: Optional[str],
        is_correct: bool,
        score: Optional[float],
        max_score: Optional[float],
        difficulty: Optional[str],
    ) -> AILearningAttempt:
        """Record a learning attempt and update knowledge state."""
        student = await self.session.get(Student, student_id)
        if not student:
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Student not found")
        org_id = student.organization_id
        await self.enforcer.require_org_access(org_id)

        attempt = AILearningAttempt(
            student_id=student_id,
            organization_id=org_id,
            subject_id=subject_id,
            topic_id=topic_id,
            skill_id=skill_id,
            session_id=session_id,
            attempt_type=attempt_type,
            question=question,
            student_answer=student_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            score=score,
            max_score=max_score,
            difficulty=difficulty,
        )
        self.session.add(attempt)
        await self.session.flush()
        await self.session.refresh(attempt)

        # Update knowledge state for the topic/skill
        if topic_id or skill_id:
            await self._update_knowledge_state(
                student_id=student_id,
                org_id=org_id,
                subject_id=subject_id,
                topic_id=topic_id,
                subtopic_id=None,
                skill_id=skill_id,
                is_correct=is_correct,
            )

        await self.session.commit()
        return attempt

    async def _update_knowledge_state(
        self,
        *,
        student_id: UUID,
        org_id: UUID,
        subject_id: Optional[UUID],
        topic_id: Optional[UUID],
        subtopic_id: Optional[UUID],
        skill_id: Optional[UUID],
        is_correct: bool,
    ) -> AIStudentKnowledgeState:
        """Update (or create) a student's knowledge-state row transparently."""
        result = await self.session.execute(
            select(AIStudentKnowledgeState).where(
                AIStudentKnowledgeState.student_id == student_id,
                AIStudentKnowledgeState.organization_id == org_id,
                AIStudentKnowledgeState.subject_id == subject_id,
                AIStudentKnowledgeState.topic_id == topic_id,
                AIStudentKnowledgeState.subtopic_id == subtopic_id,
                AIStudentKnowledgeState.skill_id == skill_id,
            )
        )
        state = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if state is None:
            state = AIStudentKnowledgeState(
                student_id=student_id,
                organization_id=org_id,
                subject_id=subject_id,
                topic_id=topic_id,
                subtopic_id=subtopic_id,
                skill_id=skill_id,
                mastery_score=0.0,
                confidence=0.0,
                attempt_count=0,
                correct_answers=0,
                incorrect_answers=0,
                learning_status="NOT_STARTED",
            )
            self.session.add(state)
            await self.session.flush()

        # Transparent mastery algorithm:
        #   score change = +2 correct, -1 incorrect, bounded [0, 100]
        #   confidence = correct / attempts (bounded [0, 1])
        #   status thresholds: 0 NOT_STARTED, <40 LEARNING, <60 NEEDS_PRACTICE,
        #                    <80 DEVELOPING, >=80 MASTERED
        delta = 2.0 if is_correct else -1.0
        new_score = max(0.0, min(100.0, float(state.mastery_score) + delta))
        state.attempt_count += 1
        if is_correct:
            state.correct_answers += 1
        else:
            state.incorrect_answers += 1
        state.mastery_score = round(new_score, 2)
        state.confidence = round(state.correct_answers / state.attempt_count, 2)
        state.last_practiced_at = now
        state.last_assessed_at = now

        score = float(state.mastery_score)
        if score == 0:
            state.learning_status = "NOT_STARTED"
        elif score < 40:
            state.learning_status = "LEARNING"
        elif score < 60:
            state.learning_status = "NEEDS_PRACTICE"
        elif score < 80:
            state.learning_status = "DEVELOPING"
        else:
            state.learning_status = "MASTERED"

        state.evidence_references = json.dumps(
            {
                "source": "ai_learning_attempts",
                "attempt_count": state.attempt_count,
                "correct": state.correct_answers,
                "incorrect": state.incorrect_answers,
                "last_practiced": now.isoformat(),
            }
        )

        self.session.add(state)
        await self.session.flush()
        await self.session.refresh(state)
        return state
