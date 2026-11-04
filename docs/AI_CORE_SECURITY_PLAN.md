# AI Core Security Plan — EduMind AI (Phase 2)

## Scope
Security for all seven AI Core components: System Prompt, RAG, MCP, Access Control, Cache, Trace, plus Model Provider abstraction.

## Identity & authentication (reuse Phase 1)
- AI Core routes reuse Phase 1 `get_current_user()` (HttpOnly `access_token` cookie or `Authorization: Bearer` header).
- No parallel user database; no separate AI passwords/tokens.
- Session revocation via Phase 1 `user_sessions` applies to AI Core too.
- Short-lived access tokens; rotating refresh tokens.

## Authorization (backend-enforced)
- Reuses Phase 1 `OrganizationMembership.role` (SUPER_ADMIN, SCHOOL_ADMIN, TEACHER, STUDENT, PARENT).
- `organization_id` resolved server-side from user's active membership — **never trusted from client**.
- Role-based prompt selection (STUDENT/TEACHER/PARENT/SCHOOL_ADMIN/SUPER_ADMIN).
- MCP tools: read-only by default; write requires separate authorization.
- Every AI repository query filters by `organization_id`.
- Tests required for privilege escalation and cross-tenant access.

## Input security
- Request size limits on all AI endpoints.
- File upload validation: size, extension, MIME type (magic bytes, not client-provided).
- Safe text normalization; no execution of uploaded document content.
- Malformed requests → 400/422 without internal details.

## Prompt injection defense (multi-layer)
1. **System prompt immutability**: User messages and retrieved RAG document content cannot overwrite or override the composed system prompt. Prompt template placeholders use safe substitution (no raw user interpolation into system instructions).
2. **RAG documents treated as untrusted**: Retrieved chunks are inserted into the user-message portion of the prompt, never the system portion. Clear delimiter between system instructions and retrieved context.
3. **No secret exposure**: System prompts never contain API keys, DB credentials, or internal endpoints.
4. **Keyword + behavioral detection**: Not keyword-only; combined with least-privilege tool access and output validation.
5. **Tool-call gating**: MCP tool execution requires explicit permission; retrieved document content cannot trigger tool calls.

## Output security
- Response structure validated against schema before returning.
- PII filtering: student personal data redacted from AI responses unless the requester is authorized.
- Internal prompt leak protection: system prompt/templates never echoed back to users.
- Source/citation validation: only real, access-checked document references returned; no fabricated sources.
- Error responses: generic messages to clients; detailed errors logged server-side without secrets.

## Data security
- No passwords, access tokens, or API keys in logs (application, audit, trace).
- No API keys in source code; all via environment variables / secret references.
- Minimal data collection: traces store anonymized query hashes, not raw text; no full private student content.
- Secure deletion: soft-deleted documents cascade to chunks + embeddings; Redis cache invalidated on delete.
- Audit of administrative AI actions (prompt changes, document deletes, tool executions).

## AI safety (minors)
- Product serves minors; no content that helps bypass school rules, reveals personal data, or generates unsafe content.
- Role-specific instructions: STUDENT responses use age-appropriate, safe educational language.
- AI does not replace official teacher grades or alter school records without authorization.
- AI does not disclose other students' information.

## Redis cache security
- Cache keys namespaced by organization (`ai:{org_id}:{namespace}:{key}`).
- No cross-user caching of permission-dependent or personal responses.
- No secret caching.
- TTL on all cache entries; invalidation on data change.
- Fallback to uncached path when Redis unavailable (no silent data exposure).
- Hit/miss logged without content.

## Trace security
- OpenTelemetry spans exclude: passwords, access tokens, API keys, full private content.
- Trace metadata table stores only trace_id, operation, status, latency — no payloads.
- Traces org-scoped; users see only their org's traces.

## Dependency / supply chain
- `pip audit` / `npm audit` run as part of checks (documented).
- Dependencies pinned; pgvector provider optional/abstracted.

## Security testing (mandatory)
- Prompt injection attempts (system override via user message / RAG document).
- Cross-tenant document access (org A user querying org B chunks).
- Cross-tenant cache leakage.
- Unauthorized MCP tool execution (student calling school_admin tool).
- Privilege escalation (role manipulation via client params).
- Sensitive data leakage in responses/traces/logs.
- Malicious uploaded documents (exec attempt, oversized, bad MIME).

## Known gaps (to validate in Docker-enabled environment)
- HTTPS/Secure cookie enforcement requires TLS termination (Nginx); `COOKIE_SECURE=false` in dev.
- pgvector extension availability to be confirmed; Vector Store abstracted for fallback.
