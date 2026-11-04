# Learning Analytics — Documentation

## Overview

Learning Analytics provides role-scoped insights into learning progress using real database aggregations. Missing information is distinguished from zero values (None vs 0).

## Student Analytics

| Field | Description |
|-------|-------------|
| average_score | Average grade score (None if no grades) |
| grade_count | Number of grades |
| attendance_by_status | Count per attendance status |
| submission_count | Assignment submissions |
| mastery_by_topic | Topic → mastery score |
| topics_needing_practice | Topics with mastery < 60 |
| recent_errors | Last 5 error analyses |
| active_paths | Number of active learning paths |

## Teacher Analytics

| Field | Description |
|-------|-------------|
| classes | List of teacher's classes with stats |
| total_students | Total students across classes |
| overall_average_score | Average of class averages |

## Parent Analytics

| Field | Description |
|-------|-------------|
| children | Verified children with their analytics |

Each child shows: average_score, attendance_rate, mastery_by_topic, recent_errors.

## School Analytics (Admin)

| Field | Description |
|-------|-------------|
| student_count | Total students |
| teacher_count | Total teachers |
| class_count | Total classes |
| average_score | Organization-wide average |

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/ai/analytics/student/{id}` | Student analytics | Student/staff |
| GET | `/api/v1/ai/analytics/teacher/{id}` | Teacher analytics | Staff only |
| GET | `/api/v1/ai/analytics/parent/{id}` | Parent analytics | Parent/staff |
| GET | `/api/v1/ai/analytics/school/{org_id}` | School analytics | Admin only |

## Access Control

- Student: own analytics only
- Teacher: assigned classes' analytics
- Parent: verified children only
- School Admin: own organization
- Cross-tenant access denied

## Guardrails

- No public shaming, comparison, or labeling of students
- Missing information distinguished from zero values (None vs 0)
- No hidden profiling

## Frontend

Page: `frontend/app/[locale]/ai-analytics/page.tsx`
- Student/teacher/parent view tabs
- Score cards (average, grades, submissions, paths)
- Topics needing practice
- Recent errors
- Class progress table (teacher)
- Children overview (parent)

## Testing

Tests in `backend/tests/test_phase3.py`:
- `test_student_analytics` — student analytics retrieval
- `test_school_analytics_admin` — school analytics (admin)
- `test_analytics_cross_tenant_denied` — cross-tenant access denied

## Status

IMPLEMENTED / TESTED — All routes, models, and tests pass.
