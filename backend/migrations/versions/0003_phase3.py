"""phase 3 ai integration schema

Revision ID: 0003_phase3
Revises: 0002_ai_core
Create Date: 2026-11-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_phase3"
down_revision: Union[str, None] = "0002_ai_core"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    # ---------- AI Tutor sessions ----------
    op.create_table(
        "ai_tutor_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="uz"),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_tutor_sessions_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_tutor_sessions_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], name=op.f("fk_ai_tutor_sessions_subject_id_subjects"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name=op.f("fk_ai_tutor_sessions_topic_id_topics"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_tutor_sessions")),
        sa.CheckConstraint("mode IN ('explain','step_by_step','practice','quiz','exam_preparation','homework_help','revision')", name=op.f("ck_ai_tutor_sessions_mode")),
        sa.CheckConstraint("language IN ('uz','ru','en')", name=op.f("ck_ai_tutor_sessions_locale")),
    )
    op.create_index(op.f("ix_ai_tutor_sessions_student_id"), "ai_tutor_sessions", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_tutor_sessions_organization_id"), "ai_tutor_sessions", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_tutor_sessions_is_active"), "ai_tutor_sessions", ["is_active"], unique=False)
    op.create_index(op.f("ix_ai_tutor_sessions_created_at"), "ai_tutor_sessions", ["created_at"], unique=False)

    # ---------- AI Tutor messages ----------
    op.create_table(
        "ai_tutor_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("citations", sa.Text(), nullable=True),  # JSON text
        sa.Column("provider", sa.String(length=60), nullable=True),
        sa.Column("usage", sa.Text(), nullable=True),  # JSON text
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["ai_tutor_sessions.id"], name=op.f("fk_ai_tutor_messages_session_id_ai_tutor_sessions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_tutor_messages")),
        sa.CheckConstraint("role IN ('user','assistant','system')", name=op.f("ck_ai_tutor_messages_role")),
    )
    op.create_index(op.f("ix_ai_tutor_messages_session_id"), "ai_tutor_messages", ["session_id"], unique=False)
    op.create_index(op.f("ix_ai_tutor_messages_created_at"), "ai_tutor_messages", ["created_at"], unique=False)

    # ---------- Knowledge Map: subjects ----------
    op.create_table(
        "ai_knowledge_subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_knowledge_subjects_organization_id_organizations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_knowledge_subjects")),
        sa.UniqueConstraint("organization_id", "name", name=op.f("uq_ai_knowledge_subjects_organization_id_name")),
    )

    # ---------- Knowledge Map: topics ----------
    op.create_table(
        "ai_knowledge_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["ai_knowledge_subjects.id"], name=op.f("fk_ai_knowledge_topics_subject_id_ai_knowledge_subjects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_knowledge_topics")),
    )
    op.create_index(op.f("ix_ai_knowledge_topics_subject_id"), "ai_knowledge_topics", ["subject_id"], unique=False)

    # ---------- Knowledge Map: subtopics ----------
    op.create_table(
        "ai_knowledge_subtopics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["ai_knowledge_topics.id"], name=op.f("fk_ai_knowledge_subtopics_topic_id_ai_knowledge_topics"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_knowledge_subtopics")),
    )
    op.create_index(op.f("ix_ai_knowledge_subtopics_topic_id"), "ai_knowledge_subtopics", ["topic_id"], unique=False)

    # ---------- Knowledge Map: skills ----------
    op.create_table(
        "ai_knowledge_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtopic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["subtopic_id"], ["ai_knowledge_subtopics.id"], name=op.f("fk_ai_knowledge_skills_subtopic_id_ai_knowledge_subtopics"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_knowledge_skills")),
    )
    op.create_index(op.f("ix_ai_knowledge_skills_subtopic_id"), "ai_knowledge_skills", ["subtopic_id"], unique=False)

    # ---------- Student knowledge state ----------
    op.create_table(
        "ai_student_knowledge_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subtopic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mastery_score", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incorrect_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_practiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("learning_status", sa.String(length=30), nullable=False, server_default="NOT_STARTED"),
        sa.Column("evidence_references", sa.Text(), nullable=True),  # JSON text
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_student_knowledge_state_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_student_knowledge_state_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["ai_knowledge_subjects.id"], name=op.f("fk_ai_student_knowledge_state_subject_id_ai_knowledge_subjects"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["ai_knowledge_topics.id"], name=op.f("fk_ai_student_knowledge_state_topic_id_ai_knowledge_topics"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subtopic_id"], ["ai_knowledge_subtopics.id"], name=op.f("fk_ai_student_knowledge_state_subtopic_id_ai_knowledge_subtopics"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["skill_id"], ["ai_knowledge_skills.id"], name=op.f("fk_ai_student_knowledge_state_skill_id_ai_knowledge_skills"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_student_knowledge_state")),
        sa.CheckConstraint("mastery_score >= 0 AND mastery_score <= 100", name=op.f("ck_ai_student_knowledge_state_mastery_score")),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name=op.f("ck_ai_student_knowledge_state_confidence")),
        sa.CheckConstraint("learning_status IN ('NOT_STARTED','LEARNING','NEEDS_PRACTICE','DEVELOPING','MASTERED')", name=op.f("ck_ai_student_knowledge_state_learning_status")),
        sa.UniqueConstraint("student_id", "subject_id", "topic_id", "subtopic_id", "skill_id", name=op.f("uq_ai_student_knowledge_state_student_subject_topic_subtopic_skill")),
    )
    op.create_index(op.f("ix_ai_student_knowledge_state_student_id"), "ai_student_knowledge_state", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_student_knowledge_state_organization_id"), "ai_student_knowledge_state", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_student_knowledge_state_learning_status"), "ai_student_knowledge_state", ["learning_status"], unique=False)

    # ---------- Learning attempts ----------
    op.create_table(
        "ai_learning_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_type", sa.String(length=30), nullable=False),  # practice/quiz/exam/homework
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("student_answer", sa.Text(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("max_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("difficulty", sa.String(length=20), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_learning_attempts_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_learning_attempts_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["ai_tutor_sessions.id"], name=op.f("fk_ai_learning_attempts_session_id_ai_tutor_sessions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["ai_knowledge_subjects.id"], name=op.f("fk_ai_learning_attempts_subject_id_ai_knowledge_subjects"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["ai_knowledge_topics.id"], name=op.f("fk_ai_learning_attempts_topic_id_ai_knowledge_topics"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["skill_id"], ["ai_knowledge_skills.id"], name=op.f("fk_ai_learning_attempts_skill_id_ai_knowledge_skills"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_learning_attempts")),
        sa.CheckConstraint("attempt_type IN ('practice','quiz','exam_preparation','homework_help')", name=op.f("ck_ai_learning_attempts_attempt_type")),
    )
    op.create_index(op.f("ix_ai_learning_attempts_student_id"), "ai_learning_attempts", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_attempts_organization_id"), "ai_learning_attempts", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_attempts_session_id"), "ai_learning_attempts", ["session_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_attempts_answered_at"), "ai_learning_attempts", ["answered_at"], unique=False)

    # ---------- Error categories ----------
    op.create_table(
        "ai_error_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_error_categories")),
        sa.UniqueConstraint("code", name=op.f("uq_ai_error_categories_code")),
    )

    # ---------- Error analysis ----------
    op.create_table(
        "ai_learning_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error_type", sa.String(length=50), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("student_answer", sa.Text(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommended_exercise", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_learning_errors_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_learning_errors_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["attempt_id"], ["ai_learning_attempts.id"], name=op.f("fk_ai_learning_errors_attempt_id_ai_learning_attempts"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["error_category_id"], ["ai_error_categories.id"], name=op.f("fk_ai_learning_errors_error_category_id_ai_error_categories"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["ai_knowledge_topics.id"], name=op.f("fk_ai_learning_errors_topic_id_ai_knowledge_topics"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_learning_errors")),
        sa.CheckConstraint("error_type IN ('conceptual','calculation','reading','logic','formula','misunderstanding','incomplete','repeated')", name=op.f("ck_ai_learning_errors_error_type")),
    )
    op.create_index(op.f("ix_ai_learning_errors_student_id"), "ai_learning_errors", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_errors_organization_id"), "ai_learning_errors", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_errors_error_type"), "ai_learning_errors", ["error_type"], unique=False)
    op.create_index(op.f("ix_ai_learning_errors_created_at"), "ai_learning_errors", ["created_at"], unique=False)

    # ---------- Adaptive recommendations ----------
    op.create_table(
        "ai_adaptive_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_type", sa.String(length=50), nullable=False),  # simpler_explanation/error_analysis/harder_practice/repetition/advance
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_adaptive_recommendations_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_adaptive_recommendations_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["ai_knowledge_subjects.id"], name=op.f("fk_ai_adaptive_recommendations_subject_id_ai_knowledge_subjects"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["ai_knowledge_topics.id"], name=op.f("fk_ai_adaptive_recommendations_topic_id_ai_knowledge_topics"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_adaptive_recommendations")),
        sa.CheckConstraint("recommendation_type IN ('simpler_explanation','error_analysis','harder_practice','repetition','advance')", name=op.f("ck_ai_adaptive_recommendations_recommendation_type")),
    )
    op.create_index(op.f("ix_ai_adaptive_recommendations_student_id"), "ai_adaptive_recommendations", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_adaptive_recommendations_organization_id"), "ai_adaptive_recommendations", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_adaptive_recommendations_is_accepted"), "ai_adaptive_recommendations", ["is_accepted"], unique=False)
    op.create_index(op.f("ix_ai_adaptive_recommendations_is_dismissed"), "ai_adaptive_recommendations", ["is_dismissed"], unique=False)

    # ---------- Learning paths ----------
    op.create_table(
        "ai_learning_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("progress", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_learning_paths_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_learning_paths_student_id_students"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["ai_knowledge_subjects.id"], name=op.f("fk_ai_learning_paths_subject_id_ai_knowledge_subjects"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_topic_id"], ["ai_knowledge_topics.id"], name=op.f("fk_ai_learning_paths_target_topic_id_ai_knowledge_topics"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_learning_paths")),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name=op.f("ck_ai_learning_paths_progress")),
        sa.CheckConstraint("status IN ('active','completed','paused','archived')", name=op.f("ck_ai_learning_paths_status")),
    )
    op.create_index(op.f("ix_ai_learning_paths_student_id"), "ai_learning_paths", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_paths_organization_id"), "ai_learning_paths", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_paths_status"), "ai_learning_paths", ["status"], unique=False)

    # ---------- Learning path steps ----------
    op.create_table(
        "ai_learning_path_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(length=30), nullable=False),  # prerequisite/explanation/practice/test/repetition
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["path_id"], ["ai_learning_paths.id"], name=op.f("fk_ai_learning_path_steps_path_id_ai_learning_paths"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["ai_knowledge_topics.id"], name=op.f("fk_ai_learning_path_steps_topic_id_ai_knowledge_topics"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_learning_path_steps")),
        sa.CheckConstraint("step_type IN ('prerequisite','explanation','practice','test','repetition')", name=op.f("ck_ai_learning_path_steps_step_type")),
        sa.UniqueConstraint("path_id", "step_number", name=op.f("uq_ai_learning_path_steps_path_id_step_number")),
    )
    op.create_index(op.f("ix_ai_learning_path_steps_path_id"), "ai_learning_path_steps", ["path_id"], unique=False)

    # ---------- Learning path progress ----------
    op.create_table(
        "ai_learning_path_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_learning_path_progress_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["path_id"], ["ai_learning_paths.id"], name=op.f("fk_ai_learning_path_progress_path_id_ai_learning_paths"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["ai_learning_path_steps.id"], name=op.f("fk_ai_learning_path_progress_step_id_ai_learning_path_steps"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_learning_path_progress_student_id_students"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_learning_path_progress")),
        sa.CheckConstraint("status IN ('not_started','in_progress','completed','skipped')", name=op.f("ck_ai_learning_path_progress_status")),
        sa.UniqueConstraint("path_id", "step_id", "student_id", name=op.f("uq_ai_learning_path_progress_path_step_student")),
    )
    op.create_index(op.f("ix_ai_learning_path_progress_student_id"), "ai_learning_path_progress", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_learning_path_progress_path_id"), "ai_learning_path_progress", ["path_id"], unique=False)

    # ---------- Learning objectives ----------
    op.create_table(
        "ai_learning_objectives",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("is_achieved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["path_id"], ["ai_learning_paths.id"], name=op.f("fk_ai_learning_objectives_path_id_ai_learning_paths"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_learning_objectives")),
    )
    op.create_index(op.f("ix_ai_learning_objectives_path_id"), "ai_learning_objectives", ["path_id"], unique=False)

    # ---------- Analytics snapshots ----------
    op.create_table(
        "ai_analytics_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_type", sa.String(length=30), nullable=False),  # student/teacher/parent
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),  # JSON text
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_analytics_snapshots_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_ai_analytics_snapshots_student_id_students"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_analytics_snapshots")),
        sa.CheckConstraint("snapshot_type IN ('student','teacher','parent')", name=op.f("ck_ai_analytics_snapshots_snapshot_type")),
    )
    op.create_index(op.f("ix_ai_analytics_snapshots_organization_id"), "ai_analytics_snapshots", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_analytics_snapshots_student_id"), "ai_analytics_snapshots", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_analytics_snapshots_snapshot_date"), "ai_analytics_snapshots", ["snapshot_date"], unique=False)

    # Seed default error categories
    error_categories = [
        ("conceptual", "Conceptual Error", "Student misunderstood the underlying concept."),
        ("calculation", "Calculation Error", "Student made an arithmetic or calculation mistake."),
        ("reading", "Reading Error", "Student misread the question or condition."),
        ("logic", "Logic Error", "Student used incorrect reasoning or logic."),
        ("formula", "Formula Error", "Student applied the wrong formula."),
        ("misunderstanding", "Misunderstanding", "Student misunderstood the task requirements."),
        ("incomplete", "Incomplete Answer", "Student provided an incomplete or partial answer."),
        ("repeated", "Repeated Error", "Student repeated a previously made error."),
    ]
    for code, name, desc in error_categories:
        op.execute(
            sa.text(
                "INSERT INTO ai_error_categories (code, name, description) VALUES (:code, :name, :desc)"
            ).bindparams(code=code, name=name, desc=desc)
        )


def downgrade() -> None:
    op.drop_table("ai_analytics_snapshots")
    op.drop_table("ai_learning_objectives")
    op.drop_table("ai_learning_path_progress")
    op.drop_table("ai_learning_path_steps")
    op.drop_table("ai_learning_paths")
    op.drop_table("ai_adaptive_recommendations")
    op.drop_table("ai_learning_errors")
    op.drop_table("ai_error_categories")
    op.drop_table("ai_learning_attempts")
    op.drop_table("ai_student_knowledge_state")
    op.drop_table("ai_knowledge_skills")
    op.drop_table("ai_knowledge_subtopics")
    op.drop_table("ai_knowledge_topics")
    op.drop_table("ai_knowledge_subjects")
    op.drop_table("ai_tutor_messages")
    op.drop_table("ai_tutor_sessions")
