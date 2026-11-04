# Phase 3 Deployment — Documentation

## Overview

Deployment instructions for Phase 3 (AI Integration & Adaptive Learning).

## Prerequisites

- Docker and Docker Compose (for production)
- PostgreSQL with pgVector extension (for RAG vector store)
- Redis (for caching)
- Environment variables from `.env.example`

## Environment Variables

See `.env.example` for all required variables. Phase 3 adds no new required environment variables — it reuses Phase 1 and Phase 2 configuration.

Key variables:
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `SECRET_KEY` — JWT signing key
- `REFRESH_SECRET_KEY` — JWT refresh signing key
- `APP_ENV` — Environment (development/production)
- `DEBUG` — Debug mode
- `COOKIE_SECURE` — Set to `true` in production with HTTPS

## Running with Docker Compose

```bash
docker-compose up -d
```

Services:
- `postgres` — PostgreSQL database
- `redis` — Redis cache
- `backend` — FastAPI backend (port 8000)
- `frontend` — Next.js frontend (port 3000)

## Database Migrations

Run migrations:

```bash
cd backend
alembic upgrade head
```

This applies:
- `0001_initial` — Phase 1 tables
- `0002_ai_core` — Phase 2 AI Core tables
- `0003_phase3` — Phase 3 AI Integration tables

## Seeding Development Data

```bash
cd backend
python scripts/seed_dev.py
```

## AI Model Provider

No real AI Model Provider is connected by design. The tutor returns "[AI provider not configured]" until a provider is explicitly authorized and configured.

To connect a provider:
1. Set provider credentials in environment variables
2. Register the provider via Phase 2 `ModelProvider` abstraction
3. Restart the backend

## Security Notes

- `COOKIE_SECURE=false` in development; must be `true` in production with HTTPS
- pgVector extension availability must be confirmed for RAG vector store
- All AI Core tables carry `organization_id` for multi-tenant isolation
- Trace spans exclude passwords, tokens, and PII

## Status

PARTIALLY IMPLEMENTED — Docker Compose configuration exists but runtime validation deferred (Docker not installed locally).
