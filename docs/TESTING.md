# Testing Strategy — EduMind AI

## Backend
- Framework: Pytest + HTTPX, async support (`pytest-asyncio` style via `anyio`/FastAPI TestClient or real async client).
- Test database: isolated test database (PostgreSQL). When no local Postgres is available, tests are documented to run against a provisioned test DB; migrations applied to test DB before each run.
- Areas tested:
  1. Authentication (login, logout, refresh, password reset/change, me)
  2. Authorization (role enforcement, privileged-role self-assignment blocked)
  3. Organization isolation (cross-org access denied)
  4. Student management (CRUD, search, filter, pagination)
  5. Teacher management (profiles, assignments)
  6. Parent access (guardian verification, child-only access)
  7. Gradebook (score bounds, audit records, authorization)
  8. Homework (assignments, submissions, file validation)
  9. Timetable (overlap prevention, cancellations)
  10. Attendance (marking, history, audit)
  11. File uploads (size, extension, MIME, auth, org ownership)
  12. Analytics (real DB aggregations)
  13. Audit logs
  14. Validation errors (422)
  15. Database constraints (unique, FK, check)
- Fixtures: async engine/session, client, seeded org/users, auth headers/cookies.
- Tests run in transactions rolled back after each test where possible.

## Frontend
- Vitest + React Testing Library (unit/component).
- Playwright (end-to-end).
- Areas tested:
  1. Page rendering
  2. Authentication flows
  3. Form validation (Zod schemas)
  4. Navigation (role-based UI)
  5. Language switching (uz/ru/en)
  6. Dashboard data (mocked API via MSW or real test server)
  7. API error handling
  8. Responsive behavior
  9. Critical user workflows

## End-to-end scenarios (Playwright)
1. Create school -> create school admin -> create teacher -> create class -> create student -> enroll student.
2. Teacher creates assignment -> student submits -> teacher reviews -> teacher gives feedback.
3. Teacher creates assessment -> teacher assigns grade -> student views grade -> parent views authorized child's grade.
4. Teacher marks attendance -> student views attendance -> parent views authorized child's attendance.
5. Cross-organization access attempt -> access denied.
6. All language selections (uz, ru, en).

## Test data
- Seed data = clearly identified dev accounts + fictional student information (development/testing only).
- Never destructive against production data; isolated test database.

## Coverage goals
- All auth/authorization/organization-isolation paths: 100%.
- Core CRUD modules: high coverage.
- Run `pytest` backend and `pnpm/vitest` frontend after implementation.

## Test execution (local, no Docker)
- Backend: requires provisioned PostgreSQL; connection via `DATABASE_URL`. If unavailable, document limitation and run model/schema unit tests that do not need a live server.
- Frontend: `vitest` runnable locally; Playwright requires browsers installed.
