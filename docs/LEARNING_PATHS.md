# Personalized Learning Paths — Documentation

## Overview

Learning Paths are personalized, ordered routes toward mastering a target topic. Paths are editable — students can skip steps whose knowledge is already confirmed by results.

## Path Structure

| Field | Description |
|-------|-------------|
| id | Path UUID |
| student_id | Student UUID |
| organization_id | Organization UUID |
| subject_id | Subject UUID (optional) |
| target_topic_id | Target topic UUID (optional) |
| title | Path title |
| difficulty | Difficulty level |
| status | active / completed / paused / archived |
| progress | 0–100% |
| created_at | Creation timestamp |
| updated_at | Last update timestamp |

## Step Structure

| Field | Description |
|-------|-------------|
| id | Step UUID |
| path_id | Path UUID |
| step_number | Step order (1-based) |
| step_type | prerequisite / explanation / practice / test / repetition |
| title | Step title |
| description | Step description |
| topic_id | Topic UUID (optional) |
| is_required | Whether step is required |
| is_completed | Whether step is done |
| completed_at | Completion timestamp |

## Progress Calculation

Progress = (completed steps / total steps) × 100. When progress reaches 100%, path status changes to "completed".

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/ai/learning-paths` | Create path | Student |
| GET | `/api/v1/ai/learning-paths` | List student's paths | Student |
| GET | `/api/v1/ai/learning-paths/{id}` | Get path with steps | Student (owner) |
| PATCH | `/api/v1/ai/learning-paths/{id}` | Update path | Student (owner) |
| DELETE | `/api/v1/ai/learning-paths/{id}` | Delete path | Student (owner) |
| POST | `/api/v1/ai/learning-paths/{id}/steps/{step_id}/complete` | Complete a step | Student (owner) |
| GET | `/api/v1/ai/learning-paths/{id}/objectives` | List objectives | Student (owner) |
| POST | `/api/v1/ai/learning-paths/{id}/objectives/{obj_id}/achieve` | Mark objective achieved | Student (owner) |

## Access Control

- Student: own paths only
- Teacher: assigned classes' students
- Parent: verified children only
- School Admin: own organization

## Frontend

Page: `frontend/app/[locale]/learning-paths/page.tsx`
- Path list with progress bars
- Create new path form
- Delete path action

## Testing

Tests in `backend/tests/test_phase3.py`:
- `test_learning_path_crud` — CRUD + step completion

## Status

IMPLEMENTED / TESTED — All routes, models, and tests pass.
