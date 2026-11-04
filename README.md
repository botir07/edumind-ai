# EduMind AI

Multi-tenant Educational Management SaaS for Uzbekistan (Phase 1: Frontend + Backend, no AI).

## Supported languages
Uzbek (uz), Russian (ru), English (en) — Uzbek is a first-class language.

## Roles
SUPER_ADMIN, SCHOOL_ADMIN, TEACHER, STUDENT, PARENT.

## Modules
Electronic school diary, school management, student/teacher/parent management, academic management, gradebook, homework, timetable, attendance, learning materials, analytics, notifications.

## Tech stack
Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS, next-intl, TanStack Query, React Hook Form, Zod, Recharts, Vitest.
Backend: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, asyncpg, PostgreSQL, Redis, Pytest, HTTPX.
Infrastructure: Docker, Docker Compose, Nginx.

## Quick start (Docker)
```bash
cp .env.example .env
# edit .env with real secrets
docker compose up --build
# Backend: http://localhost:8000 (docs at /docs)
# Frontend: http://localhost:3000
```

## Quick start (local, no Docker)
```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # set DATABASE_URL to your Postgres
alembic upgrade head
uvicorn app.main:app --reload
# frontend
cd frontend
pnpm install
pnpm dev
```

## Tests
Backend: `cd backend && python -m pytest tests/ -q`
Frontend: `cd frontend && pnpm test`

## Documentation
- docs/PROJECT_AUDIT.md
- docs/IMPLEMENTATION_PLAN.md
- docs/ARCHITECTURE.md
- docs/DATABASE.md
- docs/API.md
- docs/SECURITY.md
- docs/TESTING.md
- docs/DEPLOYMENT.md
- docs/DEVELOPMENT_LOG.md
- docs/KNOWN_ISSUES.md

## AI
No AI functionality is implemented in Phase 1.
