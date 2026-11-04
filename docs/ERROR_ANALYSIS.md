# Error Analysis — Documentation

## Overview

Error Analysis helps students understand not just that they answered incorrectly, but why. It categorizes errors and provides explanations plus practice exercises.

## Error Categories

| Code | Name | Description |
|------|------|-------------|
| conceptual | Conceptual Error | Student misunderstood the underlying concept |
| calculation | Calculation Error | Student made an arithmetic mistake |
| reading | Reading Error | Student misread the question or condition |
| logic | Logic Error | Student used incorrect reasoning |
| formula | Formula Error | Student applied the wrong formula |
| misunderstanding | Misunderstanding | Student misunderstood task requirements |
| incomplete | Incomplete Answer | Student provided a partial answer |
| repeated | Repeated Error | Student repeated a previous error |

## Analysis Process

1. Receive student answer + task condition
2. Receive correct answer or verified rubric (if available)
3. Check answer against correct answer/rubric (heuristic match)
4. Determine error type (heuristic classification)
5. Map to relevant topic/subtopic
6. Check previous errors for the student on that topic
7. Produce explanation + practice exercise
8. Persist result (subject to data retention policy)

## Safety Rules

- AI does not invent correct answers. If verification is impossible, it states so explicitly.
- AI does not automatically change official school grades.
- Error categories are explainable to student and teacher.
- Output validated against schema; PII redacted.

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/ai/error-analysis` | Analyze a student answer | Student |
| GET | `/api/v1/ai/error-analysis/history` | Student's error history | Student |
| GET | `/api/v1/ai/error-analysis/{id}` | Get specific analysis | Owner or staff |
| GET | `/api/v1/ai/error-analysis/categories` | List error categories | All |

## Access Control

- Student: own analyses only
- Teacher: assigned classes' students
- Parent: verified children only
- School Admin: own organization
- Cross-tenant access denied

## Frontend

Page: `frontend/app/[locale]/error-analysis/page.tsx`
- Analysis form (question, student answer, correct answer)
- Result display (error type, explanation, recommended exercise)
- History table

## Testing

Tests in `backend/tests/test_phase3.py`:
- `test_error_analysis` — analyze answer + history + categories
- `test_error_analysis_cross_tenant_denied` — cross-tenant access denied

## Status

IMPLEMENTED / TESTED — All routes, models, and tests pass.
