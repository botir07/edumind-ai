# Phase 3 Testing — EduMind AI (AI Integration & Adaptive Learning)

## Strategy
- Backend: Pytest + HTTPX + async support.
- Test database: isolated SQLite (local, runnable without PostgreSQL) + PostgreSQL tests (skipped if no live server).
- External services (Redis, Model Provider, pgvector): tests use test doubles; integration tests **skipped with explicit reason** when service unavailable — never marked as passed.
- Frontend: Vitest + React Testing Library; Playwright E2E (deferred if browsers unavailable).

## Test categories

### Unit tests
1. Tutor orchestration (session creation, message flow, mode selection).
2. Prompt selection (STUDENT role + locale composition).
3. Knowledge state calculation (mastery score, status transitions).
4. Error classification (conceptual/calculation/reading/logic/formula/misunderstanding/incomplete/repeated).
5. Adaptive recommendation engine (decision rules applied correctly).
6. Learning path generation (ordered steps, prerequisite handling).
7. Analytics aggregation (real DB aggregations, missing vs zero).

### Integration tests
1. Phase 1 + Phase 2 + Phase 3 together (auth → access control → tutor → knowledge map → analytics).
2. AI Core request pipeline through Phase 3 endpoints.
3. RAG citations (org-scoped, access-checked).
4. MCP permissions (read-only tools, role-scoped).
5. Database persistence (Phase 3 tables, FKs, constraints).
6. Redis cache (org-namespaced, TTL, invalidation — skipped if Redis unavailable).
7. Provider adapter contracts (test doubles).
8. API authorization (every endpoint checks user + org scope).

### Security tests
1. Cross-tenant access (student/org A cannot access org B tutor sessions or knowledge map).
2. Unauthorized student access (student cannot access another student's data).
3. Parent-child relationship validation (parent sees only verified children).
4. Teacher class scope (teacher sees only assigned classes' analytics).
5. Prompt injection (tutor system prompt cannot be overridden by user message).
6. Sensitive data leakage (traces/logs/responses exclude PII, secrets, tokens).
7. Cache isolation (org A response not served to org B).
8. Session access (only owner can read/delete own tutor session).
9. Unauthorized grade modification (AI cannot change official grades).

### E2E tests (Playwright — deferred if browsers unavailable)
1. Student logs in → opens AI Tutor → asks question in Uzbek → gets explanation with source → does practice exercise → result recorded → Knowledge Map updates → error on mistake → Error Analysis created → recommendation appears → student starts Learning Path → teacher sees class analytics → parent sees child's progress.

### Test data
- Seed data = clearly identified dev accounts + fictional student information (development/testing only).
- Never destructive against production data; isolated test database.

## Execution (local, no Docker)
- Backend unit tests: runnable locally (Pytest + SQLite + test doubles).
- Backend integration tests requiring PostgreSQL/Redis/pgvector: skipped with reason if service unavailable.
- Frontend: `pnpm test` runnable locally.
- Run `pytest` backend and `pnpm test` frontend after implementation.

## Coverage goals
- Access Control / org-isolation paths: 100%.
- Security validation paths: 100%.
- Tutor orchestration / knowledge map / error analysis: high coverage.

## Reporting
Test results recorded in `docs/PHASE_3_FINAL_REPORT.md` with statuses:
- IMPLEMENTED / TESTED / PARTIALLY IMPLEMENTED / BLOCKED / NOT IMPLEMENTED
No PARTIALLY IMPLEMENTED claimed as IMPLEMENTED.
