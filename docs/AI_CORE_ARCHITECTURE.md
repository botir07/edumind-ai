# AI Core Architecture — EduMind AI (Phase 2)

## Overview
EduMind AI Core is an independent, modular AI infrastructure layer that extends the Phase 1 EduMind Platform. It contains seven mandatory components: System Prompt, RAG, MCP, Access Control, Security, Cache, Trace. It is NOT a trained neural network; language models connect later via a Model Provider Adapter.

## Design principles
- **Modular monolith extension**: `backend/app/ai_core/` lives inside the existing FastAPI backend; no microservices.
- **Reuse Phase 1 identity**: Users, organizations, memberships, roles, auth dependencies — no parallel user system.
- **No destructive changes**: New `ai_*` tables only; existing Phase 1 tables untouched.
- **Provider-agnostic**: Model Provider, Embedding Provider, Vector Store adapters behind abstract interfaces.
- **Tenant isolation**: Every AI-owned row carries `organization_id`; cross-org access denied at repository layer.
- **Security by design**: Prompt injection defense, input/output validation, PII protection, rate limiting, audit.
- **No secrets in code**: All provider API keys via environment variables; test doubles used until a provider is authorized.

## Structure
```
backend/
  app/
    ai_core/
      core/              config.py, exceptions.py, registry.py
      models/            base.py, provider.py, request.py, response.py
      system_prompt/     engine.py, templates/, policies/, versioning.py
      rag/               ingestion/, chunking/, embeddings/, retrieval/, reranking/,
                         citations/, vector_store/, pipelines/
      mcp/               server/, client/, tools/, resources/, schemas/, permissions/
      access_control/    policies/, roles/, permissions/, tenant_scope/, enforcement.py
      security/          input_validation/, prompt_injection/, output_validation/,
                         pii/, rate_limiting/, audit/
      cache/             providers/, keys.py, service.py, invalidation.py
      tracing/           context.py, spans.py, events.py, metrics.py, exporters/
      providers/         base.py, registry.py, adapters/
      orchestration/     pipeline.py, context_builder.py, request_handler.py
      api/               routes/, schemas/
      tests/
```

## Core interfaces

### Model Provider Adapter (`ai_core/providers/base.py`)
```python
class ModelProvider:
    async def generate(self, request) -> ModelResponse   # abstract
    async def health_check(self) -> bool                  # abstract
```
- Provider Registry loads configured providers; no default provider enabled.
- Test doubles used in tests; no real provider calls without authorization.

### Embedding Provider (`ai_core/rag/embeddings/base.py`)
```python
class EmbeddingProvider:
    async def embed_documents(self, texts: list[str]) -> list[list[float]]
    async def embed_query(self, text: str) -> list[float]
```

### Vector Store (`ai_core/rag/vector_store/base.py`)
```python
class VectorStore:
    async def add(self, chunks, embeddings, metadata)
    async def search(self, query_embedding, filters, top_k) -> list[ScoredChunk]
    async def delete(self, document_id)
```
- Primary adapter: PostgreSQL + pgvector (pending compatibility confirmation).
- Abstract so a non-vector fallback can be used if pgvector is unavailable.

## Component responsibilities

### 1. System Prompt Engine
Centralized prompt composition: central system prompt + role-specific + language-specific templates + policy injection + versioning + validation + audit history. Languages: uz, ru, en. Roles: STUDENT, TEACHER, PARENT, SCHOOL_ADMIN, SUPER_ADMIN. User messages cannot overwrite system rules.

### 2. RAG Engine
Ingestion (PDF, DOCX, TXT, Markdown) → chunking → embeddings → vector store → retrieval with org/subject/language/document/version metadata filtering → access check per chunk → ranking → context → citations (document, subject, page/section, source id). Missing materials explicitly reported; no fabricated sources.

### 3. MCP
Model Context Protocol server + Tool Registry. Read-only tools by default: student/teacher/parent/school-admin scoped. Each tool has strict input schema, user/org/permission checks server-side (never trust client org_id). No arbitrary SQL, shell, filesystem, or secrets access. Write operations require separate authorization.

### 4. Access Control
Reuses Phase 1 `users` + `organization_memberships`. RBAC + org isolation + resource-level + tool-level + RAG-document permissions. Role-based prompt selection. Checks on backend before retrieval and before MCP execution. No frontend-only trust.

### 5. Security
Input validation/size limits/rate limiting; prompt-injection defense (treat RAG documents as untrusted); output validation/PII filtering/internal-prompt leak protection; no secrets in logs/code; secure deletion; audit of admin actions.

### 6. Cache
Redis-backed CacheProvider with abstract interface. Request/embedding/retrieval/metadata/prompt-template caches. Keys namespaced by organization. No cross-user personal cache mixing. No secret caching. TTL + invalidation + versioning + stampede protection + Redis-down fallback. Hit/miss logged without content.

### 7. Trace
OpenTelemetry + structured logs. Every AI request gets trace_id. Spans for auth, access control, prompt composition, RAG, embedding, vector search, MCP, cache, provider, output validation, errors, latency. No passwords/tokens/API keys/full private content in traces.

## Orchestration pipeline
Incoming Request → Authentication → Access Control → Input Security → System Prompt → RAG Retrieval → MCP Tools → Cache → Model Provider → Output Security → Response + Citations → Trace + Metrics

## Integration with Phase 1
- FastAPI app factory (`main.py`) will include `ai_core.api.router` under `/api/v1/ai`.
- `get_current_user` / `require_role` reused for AI route authorization.
- `DATABASE_URL` / `REDIS_URL` reused; AI uses separate Redis DB index/namespace.
- Alembic: new migration `0002_ai_core.py` adding `ai_*` tables.

## AI boundary (Phase 2)
- No real Model Provider connected without explicit permission.
- No OpenAI/Groq/Ollama/local model downloads or calls.
- Interfaces + test doubles only; test responses clearly marked as doubles, never presented as real AI.
