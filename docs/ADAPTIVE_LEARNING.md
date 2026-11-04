# Adaptive Learning — Documentation

## Overview

Adaptive Learning generates explainable recommendations based on the student's Knowledge Map mastery states, Error Analysis results, and Learning Attempts. All recommendations carry a documented reason — no random recommendations.

## Decision Rules (Documented)

| Condition | Action | Type | Priority |
|-----------|--------|------|----------|
| Frequent errors in a topic (>=2) | Offer simpler explanation | simpler_explanation | 3 |
| Same error repeated | Offer error-analysis breakdown | error_analysis | 4 |
| Simple tasks solved successfully (>=3) | Gradually increase difficulty | harder_practice | 2 |
| Topic not practiced for >=7 days | Offer repetition | repetition | 2 |
| Topic mastered (mastery >= 80) | Advance to next related topic | advance | 1 |

## Recommendation Fields

| Field | Description |
|-------|-------------|
| id | Recommendation UUID |
| student_id | Student UUID |
| organization_id | Organization UUID |
| recommendation_type | Type of recommendation |
| title | Human-readable title |
| description | Detailed description |
| subject_id | Subject UUID (optional) |
| topic_id | Topic UUID (optional) |
| reason | Documented reason for recommendation |
| priority | Priority (1-4, higher = more urgent) |
| is_accepted | Whether student accepted |
| is_dismissed | Whether student dismissed |
| created_at | Creation timestamp |
| updated_at | Last update timestamp |

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/ai/recommendations` | List/generate recommendations | Student |
| POST | `/api/v1/ai/recommendations/{id}/accept` | Accept recommendation | Student (owner) |
| POST | `/api/v1/ai/recommendations/{id}/dismiss` | Dismiss recommendation | Student (owner) |
| GET | `/api/v1/ai/recommendations/algorithm` | Decision rule docs | Public |

## Access Control

- Student: own recommendations only
- Teacher: assigned classes' students
- Parent: verified children only
- School Admin: own organization

## Frontend

No dedicated page yet — recommendations can be accessed via the API. Future integration planned.

## Testing

Tests in `backend/tests/test_phase3.py`:
- `test_adaptive_recommendations` — generate + algorithm docs

## Status

IMPLEMENTED / TESTED — All routes, models, and tests pass.
