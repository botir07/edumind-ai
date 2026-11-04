"""ai core schema

Revision ID: 0002_ai_core
Revises: 0001_initial
Create Date: 2026-11-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_ai_core"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ai_prompt_templates
    op.create_table(
        "ai_prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="uz"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_prompt_templates_organization_id_organizations"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_prompt_templates")),
        sa.CheckConstraint("language IN ('uz','ru','en')", name=op.f("ck_ai_prompt_templates_language")),
        sa.CheckConstraint("role IN ('STUDENT','TEACHER','PARENT','SCHOOL_ADMIN','SUPER_ADMIN','platform')", name=op.f("ck_ai_prompt_templates_role")),
    )
    op.create_index(op.f("ix_ai_prompt_templates_organization_id"), "ai_prompt_templates", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_prompt_templates_role"), "ai_prompt_templates", ["role"], unique=False)
    op.create_index(op.f("ix_ai_prompt_templates_language"), "ai_prompt_templates", ["language"], unique=False)
    op.create_index(op.f("ix_ai_prompt_templates_is_active"), "ai_prompt_templates", ["is_active"], unique=False)

    # ai_prompt_versions
    op.create_table(
        "ai_prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], name=op.f("fk_ai_prompt_versions_changed_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["template_id"], ["ai_prompt_templates.id"], name=op.f("fk_ai_prompt_versions_template_id_ai_prompt_templates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_prompt_versions")),
    )
    op.create_index(op.f("ix_ai_prompt_versions_template_id"), "ai_prompt_versions", ["template_id"], unique=False)

    # ai_documents
    op.create_table(
        "ai_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=150), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="uz"),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("access_level", sa.String(length=30), nullable=False, server_default="org"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("processing_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_documents_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], name=op.f("fk_ai_documents_uploader_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_documents")),
        sa.CheckConstraint("language IN ('uz','ru','en')", name=op.f("ck_ai_documents_language")),
        sa.CheckConstraint("access_level IN ('org','class','student')", name=op.f("ck_ai_documents_access_level")),
        sa.CheckConstraint("processing_status IN ('pending','indexed','failed')", name=op.f("ck_ai_documents_processing_status")),
        sa.UniqueConstraint("organization_id", "checksum", name=op.f("uq_ai_documents_organization_id_checksum")),
    )
    op.create_index(op.f("ix_ai_documents_organization_id"), "ai_documents", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_documents_subject"), "ai_documents", ["subject"], unique=False)
    op.create_index(op.f("ix_ai_documents_language"), "ai_documents", ["language"], unique=False)
    op.create_index(op.f("ix_ai_documents_processing_status"), "ai_documents", ["processing_status"], unique=False)

    # ai_document_chunks
    op.create_table(
        "ai_document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=150), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["ai_documents.id"], name=op.f("fk_ai_document_chunks_document_id_ai_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_document_chunks")),
    )
    op.create_index(op.f("ix_ai_document_chunks_document_id"), "ai_document_chunks", ["document_id"], unique=False)
    op.create_index(op.f("ix_ai_document_chunks_chunk_index"), "ai_document_chunks", ["chunk_index"], unique=False)

    # ai_embedding_metadata
    op.create_table(
        "ai_embedding_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=60), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("vector_dim", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["ai_document_chunks.id"], name=op.f("fk_ai_embedding_metadata_chunk_id_ai_document_chunks"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_embedding_metadata")),
        sa.UniqueConstraint("chunk_id", name=op.f("uq_ai_embedding_metadata_chunk_id")),
    )

    # ai_retrieval_logs
    op.create_table(
        "ai_retrieval_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query_hash", sa.String(length=64), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_retrieval_logs_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ai_retrieval_logs_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_retrieval_logs")),
    )
    op.create_index(op.f("ix_ai_retrieval_logs_organization_id"), "ai_retrieval_logs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_retrieval_logs_created_at"), "ai_retrieval_logs", ["created_at"], unique=False)

    # ai_tool_registry
    op.create_table(
        "ai_tool_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("input_schema", sa.Text(), nullable=False),
        sa.Column("output_schema", sa.Text(), nullable=True),
        sa.Column("tool_type", sa.String(length=30), nullable=False),
        sa.Column("is_read_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("required_role", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_tool_registry")),
        sa.UniqueConstraint("name", name=op.f("uq_ai_tool_registry_name")),
        sa.CheckConstraint("tool_type IN ('student','teacher','parent','school_admin','platform')", name=op.f("ck_ai_tool_registry_tool_type")),
    )

    # ai_tool_execution_logs
    op.create_table(
        "ai_tool_execution_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(length=60), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tool_id"], ["ai_tool_registry.id"], name=op.f("fk_ai_tool_execution_logs_tool_id_ai_tool_registry"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ai_tool_execution_logs_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_ai_tool_execution_logs_organization_id_organizations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_tool_execution_logs")),
    )
    op.create_index(op.f("ix_ai_tool_execution_logs_tool_id"), "ai_tool_execution_logs", ["tool_id"], unique=False)
    op.create_index(op.f("ix_ai_tool_execution_logs_organization_id"), "ai_tool_execution_logs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_tool_execution_logs_created_at"), "ai_tool_execution_logs", ["created_at"], unique=False)

    # ai_access_policies
    op.create_table(
        "ai_access_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.String(length=60), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("effect", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_access_policies")),
        sa.CheckConstraint("effect IN ('allow','deny')", name=op.f("ck_ai_access_policies_effect")),
    )
    op.create_index(op.f("ix_ai_access_policies_organization_id"), "ai_access_policies", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_access_policies_resource_type"), "ai_access_policies", ["resource_type"], unique=False)
    op.create_index(op.f("ix_ai_access_policies_role"), "ai_access_policies", ["role"], unique=False)
    op.create_index(op.f("ix_ai_access_policies_action"), "ai_access_policies", ["action"], unique=False)

    # ai_security_events
    op.create_table(
        "ai_security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_security_events")),
        sa.CheckConstraint("severity IN ('low','medium','high','critical')", name=op.f("ck_ai_security_events_severity")),
    )
    op.create_index(op.f("ix_ai_security_events_organization_id"), "ai_security_events", ["organization_id"], unique=False)
    op.create_index(op.f("ix_ai_security_events_created_at"), "ai_security_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_ai_security_events_severity"), "ai_security_events", ["severity"], unique=False)

    # ai_cache_metadata
    op.create_table(
        "ai_cache_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ttl_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_cache_metadata")),
        sa.UniqueConstraint("namespace", "organization_id", name=op.f("uq_ai_cache_metadata_namespace_organization_id")),
    )

    # ai_trace_metadata
    op.create_table(
        "ai_trace_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operation", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_trace_metadata")),
    )
    op.create_index(op.f("ix_ai_trace_metadata_trace_id"), "ai_trace_metadata", ["trace_id"], unique=False)
    op.create_index(op.f("ix_ai_trace_metadata_created_at"), "ai_trace_metadata", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("ai_trace_metadata")
    op.drop_table("ai_cache_metadata")
    op.drop_table("ai_security_events")
    op.drop_table("ai_access_policies")
    op.drop_table("ai_tool_execution_logs")
    op.drop_table("ai_tool_registry")
    op.drop_table("ai_retrieval_logs")
    op.drop_table("ai_embedding_metadata")
    op.drop_table("ai_document_chunks")
    op.drop_table("ai_documents")
    op.drop_table("ai_prompt_versions")
    op.drop_table("ai_prompt_templates")
