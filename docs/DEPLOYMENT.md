# Deployment — EduMind AI

## Overview
EduMind AI is a modular monolith: a FastAPI backend and a Next.js frontend, with PostgreSQL and Redis. Docker Compose is the recommended local development and deployment method.

## Prerequisites
- Docker + Docker Compose (recommended), OR
- Python 3.12+, Node.js 20+, PostgreSQL 14+, Redis 7+ (manual/local without Docker)

## Environment
Copy `.env.example` to `.env` and fill in real values. Never commit `.env`.

Required variables:
- `SECRET_KEY`, `REFRESH_SECRET_KEY` — strong random strings for JWT signing
- `DATABASE_URL` — PostgreSQL async URL (postgresql+asyncpg://...)
- `TEST_DATABASE_URL` — isolated test database URL
- `REDIS_URL` — Redis URL
- `APP_ENV` — development/production/testing
- `DEBUG` — true/false
- `COOKIE_SECURE` — true when served over HTTPS (production)
- `BACKEND_CORS_ORIGINS` — allowed frontend origins
- `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD` — bootstrap super admin (change after first boot)

## Docker Compose (recommended)
```bash
cp .env.example .env
# edit .env with real secrets
docker compose up --build
```
Services: postgres, redis, backend, frontend.
- Backend runs migrations (`alembic upgrade head`) then starts uvicorn on :8000.
- Frontend starts Next.js dev server on :3000.
- Nginx can be added in front for TLS termination and static assets (see infrastructure/nginx).

## Manual local (no Docker)
1. Backend:
   ```bash
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp ../.env.example .env   # adjust DATABASE_URL to your local Postgres
   alembic upgrade head
   uvicorn app.main:app --reload
   ```
2. Frontend:
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```

## Production notes
- Set `COOKIE_SECURE=true` and serve behind HTTPS (Nginx/TLS).
- Rotate `SECRET_KEY` / `REFRESH_SECRET_KEY`.
- Restrict `BACKEND_CORS_ORIGINS`.
- Do not use the bootstrap super admin password in production.
- Set up PostgreSQL backups (pg_dump) and Redis persistence.
- Redis is used for caching/background jobs; optional in Phase 1 but configured.

## Health checks
- Backend: `GET /health` -> `{status: "ok"}`
- API docs: `GET /docs` (OpenAPI)
