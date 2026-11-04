# AI Core API — EduMind AI (Phase 2)

## Base URL
`/api/v1/ai/`

## Conventions
- REST over JSON, consistent with Phase 1 response envelope `{data, meta, error}`.
- Pydantic v2 schemas; internal SQLAlchemy models never returned directly.
- Pagination/filtering/sorting where listing.
- Proper HTTP status codes (200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500).
- OpenAPI documented at `/docs` (merged with Phase 1).
- All endpoints require authentication (reuse `get_current_user` / `require_role`).
- Administrative endpoints require SUPER_ADMIN or SCHOOL_ADMIN (org-scoped).
- No internal provider errors exposed to clients.
- No user documents/traces from other organizations exposed.

## Endpoints

### Health & config
- `GET /api/v1/ai/health` — AI Core service health (no auth required; returns dependency status only, no secrets)
- `GET /api/v1/ai/config/status` — Provider/feature enablement status (auth required; no secret values)

### System Prompt
- `GET /api/v1/ai/prompts` — List prompt templates (org-scoped; auth required)
- `POST /api/v1/ai/prompts` — Create prompt template (SUPER_ADMIN/SCHOOL_ADMIN; org-scoped)
- `GET /api/v1/ai/prompts/{prompt_id}` — Get template (auth required; org access check)
- `PATCH /api/v1/ai/prompts/{prompt_id}` — Update template (admin; creates version history)
- `DELETE /api/v1/ai/prompts/{prompt_id}` — Deactivate template (admin)

### Documents (RAG)
- `GET /api/v1/ai/documents` — List documents (org-scoped; auth required; pagination)
- `POST /api/v1/ai/documents` — Register/upload document metadata (auth required; org-scoped; file validation)
- `GET /api/v1/ai/documents/{document_id}` — Get document (auth required; org access check)
- `PATCH /api/v1/ai/documents/{document_id}` — Update metadata (auth required; owner/admin)
- `DELETE /api/v1/ai/documents/{document_id}` — Soft-delete document + chunks + embeddings (admin)
- `POST /api/v1/ai/documents/{document_id}/reindex` — Re-trigger ingestion/embedding (auth required)

### RAG
- `POST /api/v1/ai/rag/search` — Semantic search over org documents (auth required; returns chunks + citations; access-checked)
- `POST /api/v1/ai/rag/ingest` — Ingest a document (auth required; admin/teacher; file validation)

### MCP Tools
- `GET /api/v1/ai/tools` — List available MCP tools (auth required; role-scoped)
- `POST /api/v1/ai/tools/{tool_name}/execute` — Execute an MCP tool (auth required; user/org/permission checks; read-only by default)

### Traces
- `GET /api/v1/ai/traces` — List traces (auth required; org-scoped; no sensitive payloads)
- `GET /api/v1/ai/traces/{trace_id}` — Get trace summary (auth required; org access check)

### Security events
- `GET /api/v1/ai/security/events` — List security events (auth required; admin; org-scoped)

### Rate limiting
- AI endpoints rate-limited (ingest, rag/search, tool execute) to prevent abuse.

## Security notes
- Error messages do not leak internal provider details or stack traces.
- File uploads validated server-side (size, extension, MIME magic); stored outside web root.
- `organization_id` never accepted from client for scoping; resolved from user's active membership.
- No endpoint returns raw document content to unauthorized users.
- No API keys or provider secrets in responses.

## OpenAPI
Merged into Phase 1 OpenAPI at `/api/v1/openapi.json`; UI at `/docs`.
