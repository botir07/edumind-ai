# AI Tutor — Documentation

## Overview

The AI Tutor is an intelligent educational assistant that helps students learn through guided conversation. It is not an answer engine — it guides students to understanding rather than giving direct answers.

## Architecture

The AI Tutor integrates Phase 1 (students, organizations, RBAC) with Phase 2 AI Core (System Prompt, RAG, MCP, Access Control, Security, Cache, Trace, Model Provider) through Phase 3 tutor orchestration.

All AI requests flow through the Phase 2 `AIRequestHandler` pipeline:
1. Authentication (Phase 1 `get_current_user`)
2. Access Control (`AICoreEnforcer`) — student may only access own sessions + own-org materials
3. Input Security (`InputValidator`, `RateLimiter`, `PromptInjectionGuard`)
4. System Prompt (`SystemPromptEngine`) — STUDENT role + locale
5. RAG Retrieval (`RetrievalPipeline`) — optional, over student's accessible learning materials
6. MCP Tool Registry (`MCPServer`) — optional, read-only platform data access
7. Cache (`CacheService`) — optional, org-namespaced
8. Model Provider (`ModelProvider`) — test doubles unless a real provider is configured
9. Output Security (`OutputValidator`, `PIIScanner`)
10. Trace (`TraceExporter`)

## Modes

| Mode | Purpose | Behavior |
|------|---------|----------|
| explain | Explain a topic | Simple + detailed explanation, example, check question, extra exercise |
| step_by_step | Solve a problem | Break into stages, explain logic of each stage |
| practice | Training tasks | Generate similar exercises matched to mastery level |
| quiz | Short test | Small set of questions, immediate feedback, score |
| exam_preparation | Review before test | Focus on topics needing practice, spaced repetition |
| homework_help | Homework guidance | Guide student to solve themselves; hints, not final solution |
| revision | Review learned topics | Revisit mastered/developing topics |

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/ai/tutor/sessions` | Create/resume tutor session | Student |
| GET | `/api/v1/ai/tutor/sessions` | List student's sessions | Student |
| GET | `/api/v1/ai/tutor/sessions/{id}` | Get session with messages | Student (owner) |
| DELETE | `/api/v1/ai/tutor/sessions/{id}` | Delete session | Student (owner) |
| POST | `/api/v1/ai/tutor/chat` | Send message, get AI response | Student |

## Safety

- System prompt is never merged with user messages (prompt injection defense)
- RAG content treated as untrusted; inserted as user/context only
- PII redacted from responses
- No fabricated citations; only real, access-checked document references
- AI never changes official grades
- No personal student data sent to external providers without policy/consent
- If no Model Provider is configured, returns "[AI provider not configured]" — never a fake answer

## Frontend

Page: `frontend/app/[locale]/ai-tutor/page.tsx`
- Session creation and management
- Chat interface with message history
- Mode and language selection
- Provider status indicator

## Testing

Tests in `backend/tests/test_phase3.py`:
- `test_tutor_session_crud_and_chat` — session CRUD + chat (provider returns "not configured")
- `test_tutor_cross_tenant_denied` — cross-tenant session access denied

## Status

IMPLEMENTED / PARTIALLY TESTED — Backend routes and orchestration complete; no real Model Provider connected (by design).
