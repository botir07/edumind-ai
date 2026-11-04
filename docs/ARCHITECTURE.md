# Architecture — EduMind AI

## Overview
EduMind AI is a multi-tenant Educational Management SaaS (Phase 1: frontend + backend only, no AI). It uses a **Modular Monolith** architecture: a single deployable backend (FastAPI) and a single deployable frontend (Next.js), with clean module boundaries so the future AI Core can be isolated later.

## High-level structure
```
edumind-ai/
├── frontend/                 # Next.js App Router (TypeScript, Tailwind, shadcn/ui)
│   ├── app/                  # App Router routes (i18n scoped: [locale])
│   ├── components/           # Shared UI (design system)
│   ├── features/             # Feature modules (auth, dashboard, students, ...)
│   ├── hooks/                # Shared React hooks
│   ├── lib/                  # Utilities (api client, validators, i18n config)
│   ├── services/             # API service layer (TanStack Query-backed)
│   ├── messages/             # i18n JSON (uz, ru, en) — co-located with backend messages
│   ├── types/                # TypeScript types
│   └── tests/                # Vitest + RTL + Playwright
├── backend/                  # FastAPI (Python 3.12, SQLAlchemy 2.x, Alembic)
│   ├── app/
│   │   ├── api/              # API v1 routers (REST)
│   │   ├── core/             # Config, security, exceptions, dependencies
│   │   ├── database/         # Session/engine setup, base
│   │   ├── models/           # SQLAlchemy models (all modules)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── repositories/     # Data access layer
│   │   ├── services/         # Business logic per module
│   │   ├── middleware/       # Auth, tenant, request-id, error handling
│   │   ├── modules/          # Domain modules (auth, organizations, users, students, ...)
│   │   ├── ai_core/          # Future AI integration contracts (stubs, no runtime AI)
│   │   └── main.py           # FastAPI app factory
│   ├── migrations/           # Alembic migrations
│   └── tests/                # Pytest + HTTPX
├── infrastructure/           # Docker, Nginx, monitoring
├── docs/
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Backend architecture
- **App factory** (`main.py`) builds the FastAPI app, registers middleware and routers.
- **Configuration** via Pydantic Settings from environment variables (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, etc.).
- **Database**: SQLAlchemy 2.x async engine (asyncpg), async session, declarative base. `created_at`/`updated_at` on all entities. UUID primary keys (`uuid4`).
- **Layering**: API route -> Service -> Repository -> SQLAlchemy model. Routes handle HTTP; services own business logic and transactions; repositories own queries.
- **Schemas**: Pydantic v2. Internal models are never returned directly.
- **Authentication**: JWT access tokens (short-lived) + refresh tokens stored server-side; cookies HttpOnly/Secure/SameSite=Lax; password hashing Argon2id (via passlib/argon2-cffi).
- **Authorization**: centralized dependency `require_role` / organization-scoped policy; every protected endpoint validates org ownership; tenant isolation enforced in repository queries (WHERE organization_id = current org).
- **Auditing**: `audit_logs` table; every grade/attendance/assignment mutation writes an audit record.
- **Middleware**: request ID, error handling (consistent JSON error responses), auth/session, tenant resolution from JWT/subdomain or header.
- **OpenAPI**: auto-generated at `/api/v1/openapi.json`, docs at `/docs`.
- **Rate limiting**: dependency/middleware on auth endpoints.
- **ai_core**: `contracts/` and `interfaces/` define future AI integration points; no implementation, no external AI calls.

## Frontend architecture
- **Framework**: Next.js App Router, React, TypeScript.
- **Styling**: Tailwind CSS + shadcn/ui components + Lucide icons.
- **State/data**: TanStack Query (React Query) for server state; React Hook Form + Zod for forms.
- **i18n**: next-intl (or equivalent), locale segment `[locale]`, messages in `messages/{uz,ru,en}.json`, language persisted in cookie + local preference.
- **API client**: typed fetch/axios wrapper with automatic access-token cookie handling, refresh-token rotation, consistent error handling.
- **Design system**: buttons, inputs, selects, dialogs, dropdowns, tables, data cards, sidebar, breadcrumbs, pagination, toasts, skeletons, empty/error states. Deep navy/blue/violet with neutral backgrounds; light + dark theme; responsive.
- **Code splitting**: route-based (App Router) + lazy feature components.
- **Tests**: Vitest + React Testing Library (unit/component), Playwright (E2E).

## Multi-tenancy & security
- Each school = an `organization`. Users have `organization_memberships` (org + role). A user can belong to multiple orgs with different roles.
- All org-owned rows carry `organization_id`. Queries filter by the current user's active organization.
- Row-Level Security (PostgreSQL) enabled where appropriate; application-layer enforcement always present.
- No cross-org data leakage; frontend never trusted for role/org.
- Passwords: Argon2id. Tokens: short-lived access + rotating refresh. Secure cookies. CSRF on state-changing cookie-based requests.

## AI boundary (Phase 1)
`backend/app/ai_core/` contains only documented contracts/interfaces. No OpenAI/Groq/Ollama/RAG/MCP/agents/chatbot/hardcoded AI answers. The platform operates fully without AI.

## Infrastructure
- Docker Compose: frontend, backend, postgres, redis with health checks.
- Nginx: reverse proxy + static assets.
- `.env.example` documents all required variables; no committed secrets.
- Environment-based configuration; runnable locally without external cloud services.
