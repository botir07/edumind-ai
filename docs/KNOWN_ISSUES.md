# Known Issues — EduMind AI (Phase 1)

## Environment limitations (this development environment)
- Docker, PostgreSQL, and Redis servers are NOT installed locally. Docker Compose files are created and correct, but `docker compose up` could not be executed here for runtime validation. Backend/frontend were validated locally (backend tests run on SQLite via SQLAlchemy metadata; frontend builds). Validate against real PostgreSQL/Redis in a Docker-capable environment before production release.
- Backend integration tests run against a local SQLite database (aiosqlite) so the suite is executable without a provisioned Postgres. Production/development use PostgreSQL via DATABASE_URL.

## Backend
- `alembic current` / `alembic upgrade head` require a live PostgreSQL database (not available locally). Migration files are written and `alembic heads`/`history` validate offline.
- Password reset delivery channel is not wired to an external email provider in Phase 1; a dev-only `X-Dev-Reset-Token` header is returned in development to enable the reset flow without mail.
- CSRF protection for cookie-authenticated mutations is documented; SameSite=Lax cookies are used. Add explicit CSRF double-submit tokens if required by your threat model.
- File uploads are validated server-side (size, extension, MIME) and stored to a private path; actual streaming to object storage (S3) is abstracted but not implemented.

## Frontend
- Several module pages (timetable, attendance, materials, notifications, analytics, schools, users, settings, parents list, teachers list) are scaffolded placeholder pages wired to the navigation; connect them to the corresponding backend endpoints as needed.
- Playwright E2E tests are configured but browser binaries were not installed in this environment; run `npx playwright install` and `pnpm test:ui` in a capable environment.
- The design system uses custom lightweight primitives (button/input/card) rather than the full Radix-based shadcn/ui; install `@radix-ui` and `class-variance-authority` to upgrade to true shadcn/ui.

## Security
- HTTPS/Secure cookie enforcement requires TLS termination (Nginx); `COOKIE_SECURE=false` in local dev.
- No AI functionality is implemented; no student data is sent to any external AI service.

## AI Core (Phase 2)
- PostgreSQL + pgvector production vector store not validated locally (no live PostgreSQL; provider-agnostic interface ready, PgVectorStore adapter unwired until extension confirmed).
- Docker Compose runtime not validated locally (Docker not installed in this environment).
- No real AI Model Provider connected (by design; interfaces + test doubles only).
- Playwright E2E configured but browser binaries not installed locally (`pnpm test:ui` deferred).
- PostgreSQL/Redis integration tests skipped locally (MemoryCacheProvider + SQLite used instead); documented in AI_CORE_TESTING.md.
- OpenTelemetry collector integration deferred (lightweight structured-log TraceExporter implemented).

## AI
None implemented as a trained neural network (Phase 1 & 2 boundary). AI Core is infrastructure only; language model connects later via a Model Provider Adapter (Phase 3, requires explicit authorization).
