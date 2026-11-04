"""Phase 3 AI Integration SQLAlchemy models.

These mirror Alembic migration 0003_phase3. Registered on the same
DeclarativeBase as Phase 1 + Phase 2 models. No Phase 1/Phase 2 tables altered.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AITutorSession(Base):
    """An AI tutoring session for a student."""

    __tablename__ = "ai_tutor_sessions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(30), nullable=False)  # explain/step_by_step/practice/quiz/exam_preparation/homework_help/revision
    locale: Mapped[str] = mapped_column(String(10), nullable=False, server_default="uz")
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AITutorSession {self.id} student={self.student_id} mode={self.mode}>"


class AITutorMessage(Base):
    """A message within a tutoring session."""

    __tablename__ = "ai_tutor_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_tutor_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user/assistant/system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    citations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON text
    provider: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    usage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON text
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AITutorMessage {self.id} session={self.session_id} role={self.role}>"


class AIKnowledgeSubject(Base):
    """A subject in the knowledge map."""

    __tablename__ = "ai_knowledge_subjects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIKnowledgeSubject {self.name}>"


class AIKnowledgeTopic(Base):
    """A topic within a knowledge-map subject."""

    __tablename__ = "ai_knowledge_topics"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_subjects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIKnowledgeTopic {self.name}>"


class AIKnowledgeSubtopic(Base):
    """A subtopic within a knowledge-map topic."""

    __tablename__ = "ai_knowledge_subtopics"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_topics.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIKnowledgeSubtopic {self.name}>"


class AIKnowledgeSkill(Base):
    """A skill within a knowledge-map subtopic."""

    __tablename__ = "ai_knowledge_skills"

    subtopic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_subtopics.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIKnowledgeSkill {self.name}>"


class AIStudentKnowledgeState(Base):
    """A student's mastery state for a knowledge-map node."""

    __tablename__ = "ai_student_knowledge_state"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject_id", "topic_id", "subtopic_id", "skill_id",
            name="uq_ai_student_knowledge_state_student_subject_topic_subtopic_skill",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_subjects.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_topics.id", ondelete="SET NULL"), nullable=True
    )
    subtopic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_subtopics.id", ondelete="SET NULL"), nullable=True
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_skills.id", ondelete="SET NULL"), nullable=True
    )
    mastery_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, server_default="0")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    incorrect_answers: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    learning_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NOT_STARTED")
    evidence_references: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON text
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIStudentKnowledgeState student={self.student_id} status={self.learning_status}>"


class AILearningAttempt(Base):
    """A student's attempt at a practice/quiz/exam question."""

    __tablename__ = "ai_learning_attempts"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_subjects.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_topics.id", ondelete="SET NULL"), nullable=True
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_skills.id", ondelete="SET NULL"), nullable=True
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_tutor_sessions.id", ondelete="SET NULL"), nullable=True
    )
    attempt_type: Mapped[str] = mapped_column(String(30), nullable=False)  # practice/quiz/exam_preparation/homework_help
    question: Mapped[str] = mapped_column(Text, nullable=False)
    student_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    max_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AILearningAttempt {self.id} student={self.student_id} correct={self.is_correct}>"


class AIErrorCategory(Base):
    """A category of learning error."""

    __tablename__ = "ai_error_categories"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIErrorCategory {self.code}>"


class AILearningError(Base):
    """An error analysis record for a student attempt."""

    __tablename__ = "ai_learning_errors"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_learning_attempts.id", ondelete="SET NULL"), nullable=True
    )
    error_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_error_categories.id", ondelete="SET NULL"), nullable=True
    )
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)  # conceptual/calculation/reading/logic/formula/misunderstanding/incomplete/repeated
    question: Mapped[str] = mapped_column(Text, nullable=False)
    student_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_topics.id", ondelete="SET NULL"), nullable=True
    )
    recommended_exercise: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AILearningError {self.id} type={self.error_type}>"


class AIAdaptiveRecommendation(Base):
    """An adaptive learning recommendation for a student."""

    __tablename__ = "ai_adaptive_recommendations"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # simpler_explanation/error_analysis/harder_practice/repetition/advance
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_subjects.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_topics.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIAdaptiveRecommendation {self.id} type={self.recommendation_type}>"


class AILearningPath(Base):
    """A personalized learning path for a student."""

    __tablename__ = "ai_learning_paths"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_subjects.id", ondelete="SET NULL"), nullable=True
    )
    target_topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_topics.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="active")
    progress: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AILearningPath {self.id} title={self.title}>"


class AILearningPathStep(Base):
    """A step within a learning path."""

    __tablename__ = "ai_learning_path_steps"
    __table_args__ = (
        UniqueConstraint("path_id", "step_number", name="uq_ai_learning_path_steps_path_id_step_number"),
    )

    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_learning_paths.id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(30), nullable=False)  # prerequisite/explanation/practice/test/repetition
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_knowledge_topics.id", ondelete="SET NULL"), nullable=True
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AILearningPathStep {self.id} step={self.step_number}>"


class AILearningPathProgress(Base):
    """Progress on a learning-path step for a student."""

    __tablename__ = "ai_learning_path_progress"
    __table_args__ = (
        UniqueConstraint("path_id", "step_id", "student_id", name="uq_ai_learning_path_progress_path_step_student"),
    )

    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_learning_paths.id", ondelete="CASCADE"), nullable=False
    )
    step_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_learning_path_steps.id", ondelete="SET NULL"), nullable=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="not_started")
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AILearningPathProgress student={self.student_id} status={self.status}>"


class AILearningObjective(Base):
    """A learning objective within a path."""

    __tablename__ = "ai_learning_objectives"

    path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_learning_paths.id", ondelete="CASCADE"), nullable=False
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    is_achieved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    achieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AILearningObjective {self.id}>"


class AIAnalyticsSnapshot(Base):
    """A cached analytics snapshot."""

    __tablename__ = "ai_analytics_snapshots"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=True
    )
    snapshot_type: Mapped[str] = mapped_column(String(30), nullable=False)  # student/teacher/parent
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # date stored as timestamptz
    data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON text
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AIAnalyticsSnapshot {self.id} type={self.snapshot_type}>"
