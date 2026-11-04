# AI Core Testing — EduMind AI (Phase 2)

## Strategy
- Backend: Pytest + HTTPX + async support.
- Test database: isolated SQLite (local, runnable without Postgres) + PostgreSQL + pgvector tests (skipped if pgvector unavailable).
- External services (Redis, real Model Provider): tests use test doubles; integration tests skipped with explicit reason when service unavailable — **never marked as passed**.
- Frontend: Vitest + React Testing Library for AI Admin UI pages.

## Test categories

### Unit tests
1. System Prompt composition (role + language + policy injection).
2. Prompt versioning (create new version on change; history immutable).
3. Chunking (size, overlap, metadata preservation, document version).
4. Embedding provider interfaces (test doubles).
5. Retrieval ranking + metadata filtering.
6. MCP input schema validation.
7. RBAC (role-based access; org isolation).
8. Security validation (prompt injection detection, input sanitization).
9. Cache TTL, invalidation, namespace isolation, Redis-down fallback.
10. Trace context creation (trace_id/span_id propagation).

### Integration tests
1. Document ingestion → chunking → embedding (test double) → vector store → retrieval.
2. PostgreSQL + pgvector vector similarity + metadata filtering (skipped if pgvector unavailable).
3. Redis cache hit/miss/invalidation (skipped if Redis unavailable).
4. MCP tool execution with permission checks.
5. AI orchestration pipeline end-to-end (test doubles for provider).
6. Provider adapter contracts (health check, generate, error normalization).

### Security tests
1. Prompt injection: user message attempting to override system prompt → blocked.
2. Prompt injection: RAG document content attempting to change instructions → treated as untrusted context only.
3. Cross-tenant document access: org A user cannot retrieve org B chunks.
4. Cross-tenant cache leakage: org A response not served to org B user.
5. Unauthorized MCP tool execution: student cannot execute school_admin tool.
6. Privilege escalation: client-supplied `organization_id` / role ignored; server-resolved only.
7. Sensitive data leakage: traces/logs/responses exclude passwords, tokens, API keys, full PII.
8. Malicious uploaded documents: oversized / bad MIME / executable content rejected.

### Performance tests (documented, not fabricated)
- Retrieval latency target: < 2s for top-10 chunks (to be measured with real data).
- Cache hit latency target: < 50ms.
- Concurrent request handling (no deadlocks in repository layer).
- Database query performance with indexes (avoid N+1).

## Test data
- Seed data = clearly identified dev accounts + fictional student information (development/testing only).
- Never destructive against production data; isolated test database.

## Execution (local, no Docker)
- Backend unit tests: runnable locally (Pytest + SQLite + test doubles).
- Backend integration tests requiring Postgres/pgvector/Redis: skipped with reason if service unavailable.
- Frontend: `pnpm test` runnable locally.
- `pytest` backend and `pnpm test` frontend after implementation.

## Coverage goals
- Access Control / org-isolation paths: 100%.
- Security validation paths: 100%.
- Core orchestration: high coverage.
- RAG ingestion/retrieval: high coverage (with test doubles).

## Reporting
Test results recorded in `docs/PHASE_2_FINAL_REPORT.md` with statuses:
- IMPLEMENTED / TESTED / PARTIALLY IMPLEMENTED / BLOCKED / NOT IMPLEMENTED
No PARTIALLY IMPLEMENTED claimed as IMPLEMENTED.
