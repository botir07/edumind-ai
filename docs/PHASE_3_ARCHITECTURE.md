# Phase 3 Architecture — EduMind AI (AI Integration & Adaptive Learning)

## Overview
Phase 3 integrates EduMind AI Core (Phase 2) with the EduMind Platform (Phase 1) to create an intelligent educational platform. It implements six educational subsystems: AI Tutor, Knowledge Map, Error Analysis, Adaptive Learning, Personalized Learning Paths, and Learning Analytics. All AI capabilities flow through Phase 2 AI Core — no parallel implementations.

## Design principles
- **Integration layer on top of Phase 1 + Phase 2.** No duplication of Phase 1 (users, orgs, RBAC, school data) or Phase 2 (System Prompt, RAG, MCP, Access Control, Security, Cache, Trace).
- **Reuse Phase 2 contracts.** All AI requests flow through `AIRequestHandler` / Phase 2 components: auth, access control, input security, system prompt, RAG, cache, model provider, output security, trace.
- **No destructive database changes.** New `ai_tutor_*`, `ai_knowledge_*`, `ai_learning_*`, `ai_error_*`, `ai_path_*`, `ai_analytics_*` tables only via migration `0003_phase3`. FKs to Phase 1 `users`, `organizations`, `students`, `teachers`, `parents`, `classes`, `subjects`, `topics`, `assessments`, `grade_records`, `assignments`, `assignment_submissions`, `attendance_records`, `lessons`, `learning_materials`.
- **Provider-agnostic.** Model Provider via Phase 2 abstraction; no live provider connected without explicit authorization. No fake AI responses.
- **Multi-tenant isolation.** Every Phase 3 table carries `organization_id`; scope resolved server-side from user memberships (never trusted from client).
- **Minor safety.** RBAC enforced on backend; no public learner comparisons/rankings; AI never changes official grades; no hidden profiling.

## Structure
```
backend/
  app/
    ai_core/                          (Phase 2 — reused, not modified)
      system_prompt/, rag/, mcp/, access_control/,
      security/, cache/, tracing/, providers/,
      orchestration.py, core/, models/, api/
    modules/
      ai_tutor/                       (NEW — Phase 3)
        router.py, service.py, schemas.py
      ai_knowledge_map/               (NEW — Phase 3)
        router.py, service.py, schemas.py
      ai_error_analysis/              (NEW — Phase 3)
        router.py, service.py, schemas.py
      ai_adaptive_learning/           (NEW — Phase 3)
        router.py, service.py, schemas.py
      ai_learning_paths/              (NEW — Phase 3)
        router.py, service.py, schemas.py
      ai_analytics/                   (NEW — Phase 3)
        router.py, service.py, schemas.py
    models/
      tables.py                       (Phase 1 + Phase 2 + Phase 3 ai_* tables)
    api/v1/api.py                     (Phase 3 routers added)
  migrations/
    versions/0003_phase3.py           (NEW — Phase 3 tables)
frontend/
  app/[locale]/ai-tutor/              (NEW — Phase 3 pages)
  app/[locale]/knowledge-map/         (NEW — Phase 3 pages)
  app/[locale]/learning-paths/        (NEW — Phase 3 pages)
  app/[locale]/error-analysis/        (NEW — Phase 3 pages)
  app/[locale]/ai-analytics/          (NEW — Phase 3 pages)
  lib/ai.ts                           (Phase 2 — extended with Phase 3 endpoints)
```

## Six educational subsystems

### 1. AI Tutor
Educational chat through Phase 2 orchestration pipeline. Modes: explain, step-by-step, practice, quiz, exam-preparation, homework-help, revision. Uses System Prompt (STUDENT role + locale), RAG (learning materials), MCP (student's own grades/timetable/homework — read-only), Cache, Model Provider, Output Security, Trace. Does NOT auto-solve homework; guides learning. Sessions + messages persisted.

### 2. Knowledge Map
Subject → Topic → Subtopic → Skill hierarchy. Per-student mastery state: mastery score, confidence, attempt count, correct/incorrect answers, last practiced/assessed dates, learning status (NOT_STARTED/LEARNING/NEEDS_PRACTICE/DEVELOPING/MASTERED), evidence references. Computed transparently from real attempt data, not just school grades.

### 3. Error Analysis
Analyzes incorrect answers: conceptual / calculation / reading / logic / formula / misunderstanding / incomplete / repeated. Checks condition, correct answer/rubric, determines error type, maps to topic, checks previous errors, produces explanation + practice exercise. Does not fabricate correct answers; states when verification is impossible. Does not change official grades.

### 4. Adaptive Learning
Documents decision rules: frequent errors → simpler explanation; repeated same error → error analysis; simple successes → gradual difficulty increase; stale topic → repetition; mastered topic → advance to related topic. Produces explainable recommendations. Teacher views class-level recommendations within permitted scope.

### 5. Personalized Learning Paths
Ordered steps toward a target topic: prerequisite check, explanation, practice, test. Per-path: ID, student, subject, target topic, objectives, steps, difficulty, progress, status, dates. Editable. Skips steps whose knowledge is already confirmed.

### 6. Learning Analytics
Student/teacher/parent dashboards with real DB aggregations: overall progress, per-subject progress, mastered/topics-needing-practice, recent errors, recommended exercises, active paths, activity history. Teacher sees class-level distribution + students needing help (within assigned classes). Parent sees only verified children. No public shaming/ranking.

## Integration with Phase 2 components

| Phase 3 subsystem | Uses Phase 2 component | How |
|-------------------|----------------------|-----|
| AI Tutor | SystemPromptEngine | STUDENT-role + locale prompt for tutor |
| AI Tutor | RetrievalPipeline | RAG over student's accessible learning materials |
| AI Tutor | MCPServer | Read-only: my grades, my timetable, my homework |
| AI Tutor | CacheService | Cache non-personal tutor responses (org-namespaced) |
| AI Tutor | ModelProvider | LLM generation (not configured → "[AI provider not configured]") |
| AI Tutor | OutputValidator + PIIScanner | Redact PII, strip internal prompt echo |
| AI Tutor | TraceExporter | Trace every tutor turn |
| AI Tutor | AICoreEnforcer | Student may only access own data + own org materials |
| Knowledge Map | SecurityAuditor | Audit mastery-state changes |
| Error Analysis | OutputValidator | Validate analysis output structure |
| Adaptive Learning | CacheService | Cache recommendations per student |
| Learning Analytics | TraceExporter | Trace analytics queries |

## AI boundary (Phase 3)
- **No real Model Provider connected.** Phase 2 `ModelProvider` abstraction used; no provider enabled by default. AI Tutor returns "[AI provider not configured]" with a clear message. No OpenAI/Groq/Ollama/local model calls without explicit authorization.
- **No fake AI responses.** Test doubles only; clearly marked as not configured.
- **No personal student data sent to external providers** without policy/consent.
