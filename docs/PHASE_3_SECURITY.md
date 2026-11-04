# Phase 3 Security Plan — EduMind AI

## Scope
Security for all six Phase 3 educational subsystems (AI Tutor, Knowledge Map, Error Analysis, Adaptive Learning, Personalized Learning Paths, Learning Analytics), building on Phase 2 Security.

## Identity & authentication (reuse Phase 1 + Phase 2)
- Phase 3 API routes reuse Phase 1 `get_current_user()` (HttpOnly `access_token` cookie or `Authorization: Bearer` header).
- No parallel user database.
- Session revocation via Phase 1 `user_sessions` applies to Phase 3 too.

## Authorization (backend-enforced, never frontend-only)
- Reuses Phase 1 `OrganizationMembership.role` + Phase 2 `AICoreEnforcer`.
- `organization_id` resolved server-side from user's active membership — **never trusted from client**.
- AI Tutor: student may only access their own sessions/messages + own-org learning materials.
- Knowledge Map: student sees own mastery; teacher sees assigned classes; parent sees verified children; school admin sees own org.
- Error Analysis: owner of the attempt + authorized staff.
- Adaptive Learning: owner of recommendations + teacher of assigned classes.
- Learning Paths: owner + authorized staff.
- Learning Analytics: role-scoped (student/teacher/parent/school-admin).
- Tests required for cross-tenant access and privilege escalation.

## Input security
- Request size limits on all Phase 3 endpoints.
- Tutor message length limits (Phase 2 `prompt_max_length`).
- Safe text normalization; no execution of user content.
- Malformed requests → 400/422 without internal details.

## Prompt injection defense (multi-layer, extends Phase 2)
1. **System prompt immutability**: User messages and RAG content never merged into the system prompt; delivered as user/context only.
2. **RAG documents treated as untrusted**: Retrieved chunks inserted into user-message portion, with system delimiters stripped.
3. **No secret exposure**: System prompts never contain API keys/DB credentials/internal endpoints.
4. **Keyword + behavioral detection**: Not keyword-only; combined with least-privilege tool access and output validation.
5. **Tutor turn gating**: Each turn re-validates input; injection attempt → `AISecurityError`, audit event.

## Output security
- Response structure validated against schema before returning.
- PII filtering: student personal data redacted unless requester is authorized.
- Internal prompt leak protection: system prompt/templates never echoed back.
- Citation validation: only real, access-checked document references returned; no fabricated sources.
- Generic client error messages; detailed errors logged server-side without secrets.

## Data security (minors)
- No passwords, access tokens, API keys in logs (application, audit, trace).
- No API keys in source code; all via environment variables.
- Minimal data collection: traces store anonymized query hashes, not raw text.
- Secure deletion: soft-deleted tutor sessions/messages cascade appropriately; Redis cache invalidated.
- Audit of administrative AI actions.
- No hidden profiling of students; no public rankings/labeling.

## AI safety for minors
- Age-appropriate, safe educational language (STUDENT role system prompt).
- No content that helps bypass school rules or reveals personal data.
- No unsafe content generation.
- AI does not replace official teacher grades or alter school records without authorization.

## Redis cache security
- Cache keys namespaced by organization (`ai:{org_id}:{namespace}:{key}`).
- No cross-user caching of permission-dependent or personal responses.
- No secret caching.
- TTL on all entries; invalidation on data change.
- Fallback to uncached path when Redis unavailable.
- Hit/miss logged without content.

## Trace security
- OpenTelemetry-compatible spans exclude: passwords, access tokens, API keys, full private student content.
- Trace metadata stores only trace_id, operation, status, latency — no payloads.
- Traces org-scoped.

## Dependency / supply chain
- `pip audit` / `npm audit` run as part of checks (documented).
- Dependencies pinned.

## Security testing (mandatory)
1. Prompt injection attempts via tutor message (system override → blocked).
2. Cross-tenant document/session access (org A user querying org B data → denied).
3. Cross-tenant cache leakage.
4. Unauthorized MCP tool execution (student calling school-admin tool → denied).
5. Privilege escalation (client-supplied org_id/role ignored; server-resolved only).
6. Sensitive data leakage in responses/traces/logs.
7. Unauthorized grade modification (AI cannot change official grades).
8. Parent-child validation (parent sees only verified children).

## Known gaps (to validate in Docker-enabled environment)
- HTTPS/Secure cookie enforcement requires TLS termination (Nginx); `COOKIE_SECURE=false` in dev.
- pgvector extension availability unconfirmed; Vector Store abstracted for fallback.
