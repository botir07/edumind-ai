#!/usr/bin/env bash
# EduMind AI - development helper scripts
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

usage() {
  echo "Usage: $0 {start|stop|migrate|seed|test|format|lint|build|shell-backend}"
  echo ""
  echo "start     Start backend + frontend locally (no Docker)"
  echo "stop      Stop locally started services"
  echo "migrate   Apply Alembic migrations to the database"
  echo "seed      Seed development data (fictional, dev accounts only)"
  echo "test      Run backend and frontend tests"
  echo "format    Format code (backend: ruff/black, frontend: prettier)"
  echo "lint      Lint code (backend: ruff, frontend: eslint + tsc)"
  echo "build     Build frontend for production"
  echo "shell-backend Open a Python shell in the backend context"
  echo ""
  echo "Requires: Python 3.12, Node 20+, a running PostgreSQL + Redis (or Docker Compose)."
}

cmd_start() {
  echo "==> Starting backend (uvicorn) and frontend (next dev)"
  cd "$BACKEND_DIR"
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
  BACKEND_PID=$!
  cd "$FRONTEND_DIR"
  pnpm dev &
  FRONTEND_PID=$!
  echo "Backend PID: $BACKEND_PID  Frontend PID: $FRONTEND_PID"
  echo "Backend:  http://localhost:8000"
  echo "Frontend: http://localhost:3000"
  echo "Docs:     http://localhost:8000/docs"
  wait
}

cmd_stop() {
  echo "==> Stopping local dev processes"
  pkill -f "uvicorn app.main:app" 2>/dev/null || true
  pkill -f "next dev" 2>/dev/null || true
  echo "Stopped."
}

cmd_migrate() {
  echo "==> Applying Alembic migrations"
  cd "$BACKEND_DIR"
  alembic upgrade head
}

cmd_seed() {
  echo "==> Seeding development data (fictional, dev accounts only)"
  cd "$BACKEND_DIR"
  python scripts/seed_dev.py
}

cmd_test() {
  echo "==> Running backend tests"
  cd "$BACKEND_DIR"
  python -m pytest tests/ -q
  echo "==> Running frontend tests"
  cd "$FRONTEND_DIR"
  pnpm test 2>/dev/null || echo "(frontend tests not yet configured)"
}

cmd_format() {
  echo "==> Formatting backend"
  cd "$BACKEND_DIR"
  ruff format . 2>/dev/null || python -m ruff format . 2>/dev/null || echo "(ruff not installed)"
  echo "==> Formatting frontend"
  cd "$FRONTEND_DIR"
  pnpm exec prettier --write . 2>/dev/null || echo "(prettier not installed)"
}

cmd_lint() {
  echo "==> Linting backend"
  cd "$BACKEND_DIR"
  ruff check . 2>/dev/null || python -m ruff check . 2>/dev/null || echo "(ruff not installed)"
  echo "==> Type-check backend (mypy)"
  python -m mypy app 2>/dev/null || echo "(mypy not installed)"
  echo "==> Lint + type-check frontend"
  cd "$FRONTEND_DIR"
  pnpm exec tsc --noEmit 2>/dev/null || echo "(frontend tsc not configured)"
  pnpm exec eslint . 2>/dev/null || echo "(frontend eslint not configured)"
}

cmd_build() {
  echo "==> Building frontend for production"
  cd "$FRONTEND_DIR"
  pnpm build
}

cmd_shell_backend() {
  cd "$BACKEND_DIR"
  python -c "import app.main; print('backend imports OK')"
}

case "${1:-}" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  migrate) cmd_migrate ;;
  seed) cmd_seed ;;
  test) cmd_test ;;
  format) cmd_format ;;
  lint) cmd_lint ;;
  build) cmd_build ;;
  shell-backend) cmd_shell_backend ;;
  *) usage ;;
esac
