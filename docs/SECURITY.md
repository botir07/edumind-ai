# Security — EduMind AI

## Scope
Phase 1 security review for the school management platform. AI integrations are prohibited; no student data is sent to any external AI service.

## Authentication security
- Passwords hashed with Argon2id (passlib + argon2-cffi). No plaintext or weak hashes.
- Access tokens: short-lived JWT (configurable, default 15 min).
- Refresh tokens: stored server-side (hash), rotated on use, revoked on logout, expire (configurable, default 7 days).
- Browser session cookies: `HttpOnly`, `Secure` (over HTTPS), `SameSite=Lax` (Strict where feasible), `Path=/`.
- Password reset: time-limited single-use token, delivered via configured channel (not implemented as external email in Phase 1 — endpoint exists, channel pluggable).
- Session revocation supported.
- Account activation / suspension supported.

## Authorization security
- Centralized authorization policies (FastAPI dependencies).
- Role-based access: SUPER_ADMIN, SCHOOL_ADMIN, TEACHER, STUDENT, PARENT.
- Frontend role information never trusted; every protected backend operation re-validates from the DB/session.
- Users cannot assign themselves privileged roles.
- Organization-scoped endpoints require active membership in the target organization.
- Teacher may only manage classes/subjects they are assigned to.
- Parent may only access their own verified children.

## Multi-tenant isolation
- Every org-owned table carries `organization_id`.
- Queries filter by current organization (application layer).
- PostgreSQL Row-Level Security enabled where appropriate.
- Tenant isolation tests prove cross-organization access is denied.
- No cross-org data leakage; subdomains/headers used to resolve org context where applicable.

## Input validation
- Pydantic v2 schemas on all endpoints.
- Email validation (email-validator).
- Score bounds, date ranges, file constraints validated.
- No raw SQL; SQLAlchemy ORM/parameterized queries -> SQL injection protection.

## XSS protection
- Frontend: React auto-escapes; shadcn/ui primitives; user content rendered via text, not `dangerouslySetInnerHTML`.
- Content-Type headers set correctly; CSP considered for Nginx.

## CSRF protection
- State-changing cookie-based endpoints require CSRF token (double-submit cookie or SameSite Strict). Implementation note: CSRF middleware added for cookie-authenticated mutations.

## Secure file uploads
- Server-side validation: file size, extension, MIME type (magic bytes, not client-provided).
- Filenames sanitized; client-provided filename never used as storage path.
- Files stored outside web root / private bucket; download via controlled endpoint.
- Private storage paths never exposed publicly.

## Rate limiting
- Rate limiting on auth endpoints (login, password reset).
- Configurable per-endpoint limits.

## Secret management
- All secrets via environment variables (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, etc.).
- `.env.example` documents variables; no real credentials committed.
- `.env` in `.gitignore`.

## Audit logging
- `audit_logs` table: actor, organization, action, target type/id, details, IP, user agent, timestamp.
- Every grade modification, attendance change, and key mutation audited within same transaction.
- Sensitive student data not logged in full (avoid PII in log details where avoidable).

## Dependency vulnerability checks
- `pip audit` / `npm audit` run as part of CI checks (documented).
- Dependencies pinned in `requirements.txt` / `package.json` with lockfiles.

## Backup, retention, deletion
- Database backup procedure documented (pg_dump schedule).
- Data retention and deletion per applicable legal/org requirements; account deletion cascades per FK policy; consent records tracked.
- Data export endpoint where authorized.

## AI boundary
- No OpenAI, Groq, OpenRouter, Ollama, model download, training, chatbot, RAG, MCP, agents, or hardcoded AI answers.
- Future AI integration isolated in `backend/app/ai_core/contracts` and `interfaces` (stubs only).

## Known gaps (to be validated in Docker-enabled environment)
- HTTPS/ Secure cookie enforcement requires TLS termination (Nginx) — documented, not locally runnable without Docker.
- Docker Compose health checks created but not executed here (Docker not installed).
