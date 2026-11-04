# AI Core Audit — EduMind AI (Phase 2)

## Audit date
2026-11-04

## Audited by
Senior AI Infrastructure Architect (autonomous team)

## Repository state at audit
- Branch: `main` (ahead of origin/main by 1 commit: `2f05d93` Phase 1)
- Working tree: clean
- No uncommitted changes

## Phase 1 platform — existing implementation

### Backend (FastAPI / Python 3.12 / SQLAlchemy 2.x)
| Component | Status |
|-----------|--------|
| App factory | `backend/app/main.py` — `create_app()`, FastAPI instance |
| Config | `backend/app/core/config.py` — Pydantic Settings, env-based |
| Security | `backend/app/core/security.py` — Argon2id, JWT access+refresh, cookies |
| Database session | `backend/app/database/session.py` — async engine (asyncpg), `get_db()` |
| Base model | `backend/app/database/base.py` — UUID PK, created_at/updated_at |
| Models | 31 tables under `backend/app/models/` |
| API routers | 13 routers under `backend/app/api/v1/routers/` |
| Auth service/repo | `backend/app/modules/auth/{service,repository,router}.py` |
| Dependencies | `backend/app/core/dependencies.py` — `get_current_user`, `require_role`, `get_active_memberships` |
| Migrations | `backend/migrations/versions/0001_initial.py` (Alembic) |
| Tests | `backend/tests/` — Pytest + HTTPX, SQLite in-memory, 19 tests passing |
| Requirements | `backend/requirements.txt` — pinned versions |

### Key models (reusable by AI Core, NOT to be duplicated)
| Table | Purpose for AI Core |
|-------|---------------------|
| `users` | Platform accounts — reused for AI authentication/identity |
| `organizations` | Schools — tenant root for AI data isolation |
| `organization_memberships` | User → org + role (SUPER_ADMIN, SCHOOL_ADMIN, TEACHER, STUDENT, PARENT) — reused for AI RBAC |
| `user_sessions` | Refresh token sessions — reused for session revocation |
| `audit_logs` | Immutable audit — pattern to follow for AI audit events |
| `consent_records` | GDPR consent — pattern for AI data-processing consent |
| `learning_materials` | Source documents for RAG ingestion (organization_id, subject, topic, language, file_path, is_published) |

### Auth / authorization pattern (to be reused by AI Core)
- `get_current_user()` resolves user from HttpOnly `access_token` cookie or `Authorization: Bearer` header
- `require_role(*roles)` checks active `OrganizationMembership.role` (+ SUPER_ADMIN bypass)
- `get_active_memberships()` returns user's active org memberships
- Tokens: short-lived access JWT + server-stored refresh token hash, Argon2id passwords

### API conventions (to be extended by AI Core)
- Base prefix: `/api/v1/`
- Response envelope: `{data, meta, error}`
- Pagination: `page`, `page_size` + `total`, `pages`
- Pydantic v2 schemas; internal SQLAlchemy models never returned directly
- OpenAPI at `/docs`, schema at `/api/v1/openapi.json`

### Database conventions (to be extended by AI Core)
- UUID primary keys (`uuid4`)
- `created_at`, `updated_at` (timestamptz, server default `now()`)
- `organization_id` on all org-owned tables for tenant isolation
- Foreign keys with `ON DELETE` rules; unique/check constraints; indexes
- Alembic migrations; no destructive migrations against existing data

### Frontend (Next.js 15 App Router, TypeScript, Tailwind)
| Component | Status |
|-----------|--------|
| i18n | `frontend/lib/i18n.ts`, `routing.ts`, messages `{uz,ru,en}.json` |
| Auth client | `frontend/lib/auth.tsx` — SessionProvider, login/logout/me via cookies |
| API client | `frontend/lib/api.ts` — fetch with credentials, refresh-token retry |
| UI primitives | `frontend/components/ui/{button,input,card,cn,index}.tsx` |
| Layout | `frontend/components/layout/sidebar.tsx`, `theme-provider.tsx` |
| Pages | `frontend/app/[locale]/` — login, dashboard, role-based dashboards, students, gradebook + placeholders |
| Build | `pnpm build` passes |
| Tests | `frontend/app/[locale]/login/page.test.tsx` — Vitest, 1 test passing |

### Infrastructure
| Item | Status |
|------|--------|
| `docker-compose.yml` | postgres:16-alpine, redis:7-alpine, backend, frontend; health checks |
| Dockerfiles | `infrastructure/docker/backend/Dockerfile`, `infrastructure/docker/frontend/Dockerfile` |
| `.env.example` | Documents all required env vars; no committed secrets |
| `scripts/dev.sh` | start/stop/migrate/seed/test/format/lint/build helpers |
| `scripts/seed_dev.py` | Dev accounts (fictional) — NOT for production |

### What does NOT exist yet (Phase 2 to build)
- No `backend/app/ai_core/` directory
- No AI models, no RAG, no MCP, no vector store, no pgvector
- No AI-specific database tables or Alembic migrations
- No AI API routes
- No AI security/prompt-injection/trace/cache components
- `pgvector` Python package and PostgreSQL extension not yet added

## Integration points identified (safe, non-destructive)

1. **Identity**: Reuse `users` + `organization_memberships`. No parallel user/role system.
2. **Auth**: Reuse `get_current_user()` / `require_role()` dependencies; AI routes accept the same access_token cookie/Bearer header.
3. **Database**: Add new `ai_*` tables with FKs to `users.id`, `organizations.id`; no alterations to existing Phase 1 tables.
4. **API**: Mount AI routes under `/api/v1/ai/...` alongside existing routers; reuse Pydantic v2 and response envelope conventions.
5. **Redis**: Reuse existing `REDIS_URL` for AI cache (separate DB index/namespace to avoid collisions with Phase 1).
6. **PostgreSQL**: Reuse existing server; add `pgvector` extension only if audit confirms compatibility (see database audit).
7. **Frontend**: Add AI Core Admin UI pages under `frontend/app/[locale]/ai-admin/...`; reuse i18n, design system, auth client.

## Blockers / limitations (documented honestly)
1. **Docker not installed** in this environment — `docker compose` cannot be executed locally for validation. Files created; runtime validation deferred.
2. **PostgreSQL server not installed** locally — AI Core integration tests requiring live Postgres + pgvector cannot run here unless provisioned. Tests documented to run against provisioned test DB; unit tests using interfaces/test doubles run locally.
3. **pgvector compatibility unconfirmed** — PostgreSQL 16-alpine image supports pgvector, but the extension must be verified available. Vector Store Adapter will be abstracted so a non-pgvector fallback can be used if needed.
4. **No real AI Model Provider** — Per rules, no OpenAI/Groq/Ollama/local model connections without explicit permission. Provider interfaces + test doubles only.

## Recommendation
Proceed to `docs/AI_CORE_ARCHITECTURE.md`, then implement `backend/app/ai_core/` as a modular extension of Phase 1, reusing Phase 1 identity/auth/tenant-isolation patterns without duplicating or altering existing tables.
