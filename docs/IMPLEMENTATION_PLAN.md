# Implementation Plan — EduMind AI

## Status
Initiated. Repository audit complete: repository contains only a placeholder README.md. Full stack to be built from scratch.

## Guiding constraints
- Phase 1 = Frontend + Backend only. NO AI functionality (no OpenAI/Groq/Ollama/RAG/MCP/chatbot).
- Modular Monolith. Backend (FastAPI/Python) and Frontend (Next.js) independently organized.
- PostgreSQL + SQLAlchemy 2.x + Alembic migrations. UUID PKs, FKs, unique/check constraints, indexes, created/updated timestamps.
- Multi-tenant school isolation enforced in the database and backend (never frontend-only).
- Roles: SUPER_ADMIN, SCHOOL_ADMIN, TEACHER, STUDENT, PARENT.
- Auth: Argon2id password hashing, short-lived access tokens, securely managed refresh tokens, HttpOnly/Secure/SameSite cookies, CSRF where required, centralized authorization policies.
- i18n: Uzbek (uz), Russian (ru), English (en); Uzbek is first-class.
- Environment-based config; no hardcoded credentials; `.env.example` only.
- Docker Compose for local dev (docker not installed in this env — file created, runtime validation deferred).
- Tests mandatory: backend Pytest + HTTPX; frontend Vitest + RTL + Playwright; E2E scenarios per spec.

## Implementation sequence (adapted from master prompt)
Technical dependencies require the following order; this matches the mandated steps 1–30.

| Step | Milestone | Deliverables | Acceptance criteria |
|------|-----------|--------------|---------------------|
| 1 | Repository inspection | docs/PROJECT_AUDIT.md | Done |
| 2 | Project audit | docs/PROJECT_AUDIT.md | Done |
| 3 | Architecture & implementation plan | docs/ARCHITECTURE.md, docs/IMPLEMENTATION_PLAN.md, docs/DATABASE.md, docs/API.md, docs/SECURITY.md, docs/TESTING.md | Docs complete |
| 4 | Dev environment | repo scaffold, docker-compose.yml, .env.example, scripts/, backend venv + requirements, frontend package.json | Backend imports; frontend installs |
| 5 | Database & migrations | backend/app/database, backend/app/models, backend/migrations, alembic.ini | `alembic upgrade head` applies; seed script works |
| 6 | Auth & RBAC | backend modules/auth, schemas, middleware, password hashing, JWT, refresh tokens, cookies, CSRF, role policies | Login/logout/refresh/password reset/change work; role enforcement tested |
| 7 | Organizations & academic structure | orgs, memberships, school profiles, academic years, grades, classes, subjects, topics, enrollments | Tenant isolation tests pass |
| 8 | Student & teacher management | students, teachers, profiles, employee/student numbers, class assignments, subject assignments | CRUD + search + filter + pagination |
| 9 | Parent portal | parents, guardians, verified relationships, child selection | Guardian verification; cross-child access denied |
| 10 | Gradebook | assessments, categories, grades, grade history, audit records, validation | Score bounds validated; audit on every change |
| 11 | Homework | assignments, submissions, files, feedback, resubmission | Secure file upload validation (size/ext/MIME) |
| 12 | Timetable | lessons, rooms, weekly timetable, replacements, cancellations, overlap prevention | No overlapping teacher/room slots |
| 13 | Attendance | sessions, records, present/absent/late/excused, audit, stats, export | Every change auditable |
| 14 | Learning materials | library, PDF/images/docs/external video links/text, metadata, publication status | Storage abstraction; private paths not exposed |
| 15 | Analytics | student/teacher/school analytics from real DB records | Missing vs zero distinguished |
| 16 | Frontend dashboards | student/teacher/parent/school-admin/super-admin dashboards, design system components | Responsive; role-gated data only |
| 17 | Internationalization | messages/uz.json, ru.json, en.json; next-intl; language switcher; date/number locale | All UI text via keys; no hardcoded strings |
| 18 | Integration & E2E tests | 6 E2E scenarios; backend integration tests | Critical E2E pass against isolated test DB |
| 19 | Security & performance checks | security review, indexes, connection pooling, pagination, caching of safe data | No unresolved critical vulns; N+1 avoided |
| 20 | Deployment documentation | docs/DEPLOYMENT.md, docs/DEVELOPMENT_LOG.md, docs/KNOWN_ISSUES.md, README.md | Local run + deploy instructions present |

## Phase boundaries
- Phase 1 (this effort): full school management SaaS without AI.
- Phase 2 (future): AI Core integration behind isolated contracts in `backend/app/ai_core/contracts` and `backend/app/ai_core/interfaces` (stubs only, no runtime AI).

## Definition of done per module
- Models + migrations + seed data (dev/test only)
- Pydantic schemas (no raw DB models in responses)
- API routes with pagination/filtering/sorting + consistent errors
- Backend unit + integration tests
- Authorization policy enforced + tenant-isolation test
- Frontend page(s) + form validation + i18n keys
- Frontend unit/RTL tests where applicable
- Format, lint, type-check, build, run tests — all green

## Honest documentation of unfinished work
Unfinished items will be recorded in docs/KNOWN_ISSUES.md with a clear "Not implemented / Partially implemented" status. No feature will be claimed as working without passing tests.
