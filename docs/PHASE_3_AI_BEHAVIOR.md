# Phase 3 AI Behavior — EduMind AI

## Overview
Defines the educational behavior of the AI Tutor and related subsystems. All behavior is delivered through Phase 2 AI Core components (System Prompt, RAG, MCP, Access Control, Security, Cache, Trace). No parallel AI implementation.

## Supported languages
Uzbek (uz), Russian (ru), English (en). Uzbek is first-class. Language determined from the request/locale preference; user may override manually. Persisted per user in Phase 1 `users.locale`.

## AI Tutor — educational assistant, not an answer engine

### Guiding principles (from Phase 2 safety policies, enforced in system prompt)
- Explain complex topics in simple language.
- Give step-by-step explanations.
- Help the student understand mistakes.
- Adapt to the student's knowledge level.
- Use available learning materials; cite sources.
- Do not present assumptions as verified facts.
- Do not replace official teacher grades.
- Do not alter school records without authorization.
- Do not disclose other students' information.
- Do not perform administrative actions without permission.
- Age-appropriate, safe educational responses for minors.

### Modes

| Mode | Purpose | Behavior |
|------|---------|----------|
| explain | Explain a topic | Simple language, short + detailed explanation, example, check question, extra exercise |
| step-by-step | Solve a problem | Break into stages, explain logic of each stage, do not auto-give final answer |
| practice | Training tasks | Generate similar exercises matched to student's mastery level |
| quiz | Short test | Small set of questions on a topic, immediate feedback, score |
| exam-preparation | Review before test | Focus on topics needing practice, spaced repetition, timed practice |
| homework-help | Homework guidance | Guide the student to solve themselves; hints, not the final solution |
| revision | Review learned topics | Revisit mastered/developing topics, refresh memory |

### Response structure (when appropriate)
1. Brief explanation.
2. Detailed explanation.
3. Example.
4. Check question.
5. Additional exercise.

Responses are not excessively long unless the student requests detail.

### Student context used (with permission)
- Student's knowledge map (mastery per topic).
- Student's recent errors and error analysis.
- Student's active learning paths.
- Student's grades/attendance/timetable via MCP (read-only, own data only).
- Student's accessible learning materials via RAG (own org only).

### What the tutor does NOT do
- Does not auto-solve homework or give final answers without guiding.
- Does not change official grades.
- Does not access other students' data.
- Does not bypass school rules.
- Does not present assumptions as facts.
- If a real Model Provider is not configured, returns a clear "[AI provider not configured]" message — never a fake answer.

## Knowledge Map — transparent mastery model

### Hierarchy
Subject → Topic → Subtopic → Skill (universal across subjects).

### Per-topic student state
- student_id, organization_id, subject_id, topic_id
- mastery_score (0–100, transparent algorithm)
- confidence (0–1)
- attempt_count, correct_answers, incorrect_answers
- last_practiced_date, last_assessed_date
- learning_status: NOT_STARTED / LEARNING / NEEDS_PRACTICE / DEVELOPING / MASTERED
- evidence_references (source of the assessment)

### Mastery algorithm (documented)
- mastery_score = weighted combination of correct/incorrect attempts, recency decay, and confidence.
- Correct answer increases score; incorrect decreases; repeated correct maintains.
- Score is an estimate, not objective truth; student/teacher can see why a status was assigned.
- Computed from real attempt data, not only from school grades.

## Error Analysis — understand why, not just what

### Process
1. Receive student answer + task condition.
2. Receive correct answer or verified rubric (if available).
3. Check the answer against the correct answer/rubric.
4. Determine error type: conceptual / calculation / reading / logic / formula / misunderstanding / incomplete / repeated.
5. Map to the relevant topic/subtopic.
6. Check previous errors for the student on that topic.
7. Produce an understandable explanation + a matching practice exercise.
8. Persist result (if data retention policy allows).

### Rules
- AI does not invent correct answers. If verification is impossible, it states so explicitly.
- AI does not automatically change official school grades.
- Error categories are explainable to student and teacher.

## Adaptive Learning — explained recommendations

### Documented decision rules
| Condition | Action |
|-----------|--------|
| Frequent errors in a topic | Offer simpler explanation |
| Same error repeated | Offer error-analysis breakdown |
| Simple tasks solved successfully | Gradually increase difficulty |
| Topic not practiced for a while | Offer repetition |
| Topic mastered | Advance to the next related topic |

### Explainability
- Every recommendation carries a reason (e.g., "You missed 3 linear-equation attempts; here's a simpler explanation").
- Teacher can view class-level recommendations within assigned classes.
- No random recommendations.

## Personalized Learning Paths

### Structure
- path_id, student_id, subject, target_topic, learning_objectives, ordered steps, difficulty, progress, status, created/updated dates.
- Example path to master quadratic equations: prerequisite check → linear equations review → explanation → formula → simple exercises → medium → hard → final test → analysis → repetition if needed.

### Rules
- Paths are editable.
- Skip steps whose knowledge is already confirmed by results.
- Student can see progress; teacher can view assigned paths within scope.

## Learning Analytics — real data, role-scoped

### Student
- Overall progress, per-subject progress, mastered topics, topics needing practice, recent errors, recommended exercises, active paths, activity history.

### Teacher
- Class progress, topic-mastery distribution, frequent errors, difficult topics, students needing help, success dynamics — only for assigned classes.

### Parent
- Verified children only: progress, mastered topics, recommendations, activity, overall dynamics.

### Guardrails
- No public shaming, comparison, or labeling of students.
- Missing information distinguished from zero values.

## AI safety for minors
- Age-appropriate language.
- No content that helps bypass school rules.
- No disclosure of personal data.
- No unsafe content generation.
- Role-specific system prompts (STUDENT mode is protective).

## Provider boundary
- No real Model Provider connected. If unconfigured, tutor returns "[AI provider not configured]" — never a simulated answer.
- No personal student data sent to external providers without policy and consent.
