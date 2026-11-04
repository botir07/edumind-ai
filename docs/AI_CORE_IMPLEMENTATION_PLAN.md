# AI Core Implementation Plan — EduMind AI (Phase 2)

## Status
Planning. Phase 1 platform fully implemented and committed. Phase 2 begins with audit (done) → architecture (done) → implementation.

## Implementation sequence (mandatory order per master prompt)

| Step | Milestone | Deliverables | Acceptance criteria |
|------|-----------|--------------|---------------------|
| 1 | Audit | docs/AI_CORE_AUDIT.md | Done |
| 2 | Architecture | docs/AI_CORE_ARCHITECTURE.md | Done |
| 3 | Database design | docs/AI_CORE_DATABASE.md + Alembic migration 0002_ai_core | Migration validates offline; schema matches models |
| 4 | Core interfaces | backend/app/ai_core/core/, models/, providers/base.py | Interfaces import cleanly; no circular deps |
| 5 | System Prompt Engine | system_prompt/ — engine, templates, policies, versioning | Prompt composition by role+lang; validation; audit history |
| 6 | Access Control | access_control/ — policies, roles, permissions, tenant_scope, enforcement | Reuses Phase 1 users/memberships; org isolation enforced |
| 7 | Security | security/ — input_validation, prompt_injection, output_validation, pii, rate_limiting, audit | Prompt injection tests pass; no secrets in logs |
| 8 | RAG Engine | rag/ — ingestion, chunking, embeddings, retrieval, vector_store, citations | Ingestion + retrieval tested with test doubles; org isolation |
| 9 | MCP | mcp/ — server, client, tools, resources, schemas, permissions | Read-only tools; permission checks; no arbitrary SQL/shell |
| 10 | Cache | cache/ — providers, keys, service, invalidation | Redis-backed; TTL; namespaced; fallback when Redis down |
| 11 | Trace | tracing/ — context, spans, events, metrics, exporters | OpenTelemetry spans; no secrets in traces |
| 12 | Orchestration | orchestration/ — pipeline, context_builder, request_handler | Full request flow; errors don't leak internal data |
| 13 | API | ai_core/api/routes/, schemas/ | /api/v1/ai/* routes; OpenAPI documented |
| 14 | Admin UI | frontend/app/[locale]/ai-admin/* pages | Reuses Phase 1 design system/i18n; no secrets shown |
| 15 | Tests | ai_core/tests/ + backend/tests/ | Unit + integration + security tests; pgvector tests skipped if unavailable |
| 16 | Documentation | All AI_CORE docs + README updates | Complete |
| 17 | Deployment verification | docker-compose updated; .env.example; health checks | Config correct; runtime validation deferred (no Docker locally) |

## Definition of done per component
- Interface/contract defined
- Implementation in `backend/app/ai_core/<component>/`
- Database tables + migration (if applicable)
- Unit tests (test doubles where external services needed)
- Integration tests (skipped if external service unavailable)
- Security tests (prompt injection, cross-tenant, privilege escalation)
- Docs updated
- No Phase 1 code modified or deleted

## Phase boundaries
- Phase 2 = AI Core infrastructure only. No chat UI for students (Phase 3 concern).
- No real AI provider connected.
- Test doubles clearly marked; never presented as real AI responses.

## Risks / open questions
1. pgvector availability on PostgreSQL 16-alpine — confirm; abstract Vector Store to allow fallback.
2. Docker/Postgres not installed locally — integration tests against live DB deferred; documented.
3. No authorized Model Provider — provider registry + adapters built, but no live provider enabled.
