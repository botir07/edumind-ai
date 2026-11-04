# Knowledge Map — Documentation

## Overview

The Knowledge Map tracks each student's mastery across subjects, topics, subtopics, and skills. It uses a transparent, attempt-based algorithm — not just school grades — to determine learning status.

## Structure

Subject → Topic → Subtopic → Skill (universal across subjects).

## Per-Topic Student State

| Field | Description |
|-------|-------------|
| student_id | Student UUID |
| organization_id | Organization UUID |
| subject_id | Subject UUID |
| topic_id | Topic UUID |
| subtopic_id | Subtopic UUID |
| skill_id | Skill UUID |
| mastery_score | 0–100, transparent algorithm |
| confidence | 0–1, correct/attempts |
| attempt_count | Total attempts |
| correct_answers | Correct count |
| incorrect_answers | Incorrect count |
| last_practiced_at | Last practice timestamp |
| last_assessed_at | Last assessment timestamp |
| learning_status | NOT_STARTED / LEARNING / NEEDS_PRACTICE / DEVELOPING / MASTERED |
| evidence_references | JSON, source of assessment |

## Mastery Algorithm (Documented)

- Correct answer: +2 to mastery score
- Incorrect answer: -1 to mastery score
- Score bounds: [0, 100]
- Confidence = correct_answers / attempt_count
- Status thresholds:
  - 0 → NOT_STARTED
  - <40 → LEARNING
  - <60 → NEEDS_PRACTICE
  - <80 → DEVELOPING
  - >=80 → MASTERED

Mastery score is an estimate, not objective truth. Students and teachers can see why a status was assigned via evidence references.

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/ai/knowledge-map/subjects` | Create subject | Admin/Teacher |
| GET | `/api/v1/ai/knowledge-map/subjects` | List subjects (org-scoped) | All |
| POST | `/api/v1/ai/knowledge-map/topics` | Create topic | Admin/Teacher |
| GET | `/api/v1/ai/knowledge-map/topics` | List topics | All |
| POST | `/api/v1/ai/knowledge-map/subtopics` | Create subtopic | Admin/Teacher |
| GET | `/api/v1/ai/knowledge-map/subtopics` | List subtopics | All |
| POST | `/api/v1/ai/knowledge-map/skills` | Create skill | Admin/Teacher |
| GET | `/api/v1/ai/knowledge-map/skills` | List skills | All |
| GET | `/api/v1/ai/knowledge-map/{student_id}` | Full map + mastery states | Role-scoped |
| GET | `/api/v1/ai/knowledge-map/mastery-algorithm` | Algorithm docs | Public |

## Access Control

- Student: own mastery states only
- Teacher: assigned classes' students
- Parent: verified children only
- School Admin: own organization
- Org ID resolved server-side, never trusted from client

## Frontend

Page: `frontend/app/[locale]/knowledge-map/page.tsx`
- Subject/topic/skill hierarchy view
- Mastery states table with progress bars
- Status badges (color-coded)
- Algorithm documentation link

## Testing

Tests in `backend/tests/test_phase3.py`:
- `test_knowledge_map_hierarchy` — CRUD for subjects/topics/subtopics/skills
- `test_knowledge_map_for_student` — student mastery map retrieval
- `test_mastery_algorithm_public` — algorithm docs endpoint

## Status

IMPLEMENTED / TESTED — All routes, models, and tests pass.
