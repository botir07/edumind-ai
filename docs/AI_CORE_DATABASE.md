# AI Core Database — EduMind AI (Phase 2)

## Engine
PostgreSQL (same server as Phase 1), SQLAlchemy 2.x async, Alembic migrations. New migration `0002_ai_core.py` adds only `ai_*` tables; no alterations to existing Phase 1 tables.

## Conventions
- UUID primary keys (`uuid4`).
- `created_at`, `updated_at` (timestamptz, server default `now()`) on every entity.
- `organization_id` FK to `organizations.id` on all org-owned AI tables.
- Foreign keys with `ON DELETE` rules; unique/check constraints; indexes.
- Soft deletes (`deleted_at`) where retention policy requires.
- No secrets stored in plaintext (API keys, tokens).

## AI Core tables

### ai_prompt_templates
System prompt templates.
- id (UUID PK)
- organization_id (UUID FK, nullable for platform-wide templates)
- name (String, not null)
- role (String, not null) — STUDENT/TEACHER/PARENT/SCHOOL_ADMIN/SUPER_ADMIN/platform
- language (String(10), not null) — uz/ru/en
- content (Text, not null)
- version (Integer, not null, default 1)
- is_active (Boolean, default true)
- created_at, updated_at
- Index: (organization_id, role, language, is_active)
- Check: language IN ('uz','ru','en'); role IN (...)

### ai_prompt_versions
Audit history of prompt changes.
- id (UUID PK)
- template_id (UUID FK → ai_prompt_templates.id)
- version (Integer, not null)
- content (Text, not null)
- changed_by (UUID FK → users.id, nullable)
- change_reason (Text, nullable)
- created_at (not null)

### ai_documents
Ingested documents for RAG.
- id (UUID PK)
- organization_id (UUID FK, not null)
- title (String(255), not null)
- subject (String(150), nullable)
- language (String(10), not null, default 'uz')
- source (String(100), nullable) — e.g. 'upload', 'url'
- uploader_id (UUID FK → users.id, nullable)
- access_level (String(30), not null, default 'org') — org/class/student
- version (Integer, default 1)
- checksum (String(64), not null) — SHA-256 of content
- file_path (Text, nullable) — private storage path, not public
- mime_type (String(100), nullable)
- size_bytes (BigInteger, nullable)
- processing_status (String(30), default 'pending') — pending/indexed/failed
- created_at, updated_at, deleted_at (soft delete)
- Index: (organization_id, subject, language, processing_status)
- Unique: (organization_id, checksum)

### ai_document_chunks
Chunked document content.
- id (UUID PK)
- document_id (UUID FK → ai_documents.id, ON DELETE CASCADE)
- chunk_index (Integer, not null)
- content (Text, not null)
- page (Integer, nullable)
- section (String(150), nullable)
- token_count (Integer, nullable)
- created_at
- Index: (document_id, chunk_index)

### ai_embedding_metadata
Embedding provider metadata per chunk.
- id (UUID PK)
- chunk_id (UUID FK → ai_document_chunks.id, ON DELETE CASCADE, unique)
- provider (String(60), not null)
- model (String(100), nullable)
- vector_dim (Integer, nullable)
- created_at
- Unique: chunk_id (one embedding record per chunk)

### ai_retrieval_logs
RAG retrieval audit (anonymized; no full query content if sensitive).
- id (UUID PK)
- organization_id (UUID FK, not null)
- user_id (UUID FK → users.id, nullable)
- query_hash (String(64), nullable) — hash only, not raw text
- results_count (Integer, default 0)
- latency_ms (Integer, nullable)
- created_at (not null)
- Index: (organization_id, created_at)

### ai_tool_registry
MCP tool definitions.
- id (UUID PK)
- name (String(100), not null, unique)
- description (Text, nullable)
- input_schema (JSON text, not null) — JSON Schema
- output_schema (JSON text, nullable)
- tool_type (String(30), not null) — student/teacher/parent/school_admin/platform
- is_read_only (Boolean, default true)
- is_active (Boolean, default true)
- required_role (String(30), nullable)
- created_at, updated_at

### ai_tool_execution_logs
MCP tool execution audit.
- id (UUID PK)
- tool_id (UUID FK → ai_tool_registry.id)
- user_id (UUID FK → users.id, nullable)
- organization_id (UUID FK, not null)
- success (Boolean, not null)
- error_code (String(60), nullable)
- latency_ms (Integer, nullable)
- created_at (not null)
- Index: (organization_id, created_at, tool_id)

### ai_access_policies
AI Core access policies (supplements Phase 1 RBAC).
- id (UUID PK)
- organization_id (UUID FK, nullable for platform-wide)
- resource_type (String(60), not null)
- resource_id (UUID, nullable)
- role (String(30), not null)
- action (String(60), not null) — read/write/execute/ingest/retrieve
- effect (String(10), not null) — allow/deny
- created_at, updated_at
- Unique: (organization_id, resource_type, resource_id, role, action, effect)

### ai_security_events
Security events log.
- id (UUID PK)
- organization_id (UUID FK, nullable)
- user_id (UUID FK → users.id, nullable)
- event_type (String(60), not null) — prompt_injection/rate_limit/unauthorized/...
- severity (String(20), not null) — low/medium/high/critical
- details (Text, nullable) — no secrets/PII
- ip (String(64), nullable)
- user_agent (Text, nullable)
- created_at (not null)
- Index: (organization_id, created_at, severity)

### ai_cache_metadata
Cache namespace/version tracking (optional; actual cached data in Redis).
- id (UUID PK)
- namespace (String(100), not null)
- version (Integer, default 1)
- organization_id (UUID FK, nullable)
- ttl_seconds (Integer, nullable)
- created_at, updated_at
- Unique: (namespace, organization_id)

### ai_trace_metadata
Trace sampling/config metadata (actual traces in OpenTelemetry backend).
- id (UUID PK)
- trace_id (String(64), not null, indexed)
- organization_id (UUID FK, nullable)
- user_id (UUID FK → users.id, nullable)
- operation (String(100), nullable)
- status (String(20), nullable)
- latency_ms (Integer, nullable)
- created_at (not null)
- Index: (trace_id, created_at)
- No sensitive payload stored.

### ai_provider_configs
Model provider configuration (no secrets in plaintext).
- id (UUID PK)
- name (String(100), not null, unique)
- provider_type (String(60), not null) — embedding/llm
- adapter_class (String(200), nullable)
- is_enabled (Boolean, default false)
- config_json (JSON text, nullable) — non-secret config only
- secret_ref (String(200), nullable) — env var name reference, not the secret
- created_at, updated_at

## Indexes (summary)
- ai_prompt_templates(organization_id, role, language, is_active)
- ai_documents(organization_id, subject, language, processing_status)
- ai_documents(organization_id, checksum) unique
- ai_document_chunks(document_id, chunk_index)
- ai_embedding_metadata(chunk_id) unique
- ai_retrieval_logs(organization_id, created_at)
- ai_tool_execution_logs(organization_id, created_at, tool_id)
- ai_access_policies(organization_id, resource_type, role, action)
- ai_security_events(organization_id, created_at, severity)
- ai_cache_metadata(namespace, organization_id) unique
- ai_trace_metadata(trace_id, created_at)

## Constraints (summary)
- ai_prompt_templates: language check, role check
- ai_documents: processing_status check, access_level check
- ai_tool_registry: tool_type check, is_read_only default true
- ai_access_policies: effect check (allow/deny)
- ai_security_events: severity check

## Retention policy
- ai_retrieval_logs: 90 days
- ai_tool_execution_logs: 90 days
- ai_security_events: 365 days
- ai_trace_metadata: 30 days
- Soft-deleted documents/chunks: purged after 30 days per org retention setting

## Migration
`backend/migrations/versions/0002_ai_core.py` — create_all above tables. Downgrade drops in reverse dependency order. No `drop_table` on Phase 1 tables.
