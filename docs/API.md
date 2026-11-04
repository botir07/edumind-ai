# API Design — EduMind AI

## Base URL
`/api/v1/`

## Conventions
- REST over JSON.
- Consistent response envelope: `{ "data": ..., "meta": {...}, "error": null }` for success; `{ "data": null, "meta": null, "error": { "code", "message", "details" } }` for failure.
- Pydantic v2 schemas for request validation and response serialization. Internal SQLAlchemy models never exposed directly.
- Pagination: `page`, `page_size` (or `limit`/`offset`) + `total`, `page`, `page_size`, `pages` in meta.
- Filtering & sorting via query parameters.
- Proper HTTP status codes (200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500).
- OpenAPI docs at `/docs`, schema at `/api/v1/openapi.json`.
- All mutating endpoints require authentication; organization-scoped endpoints require active membership and validate org ownership.

## Authentication (auth)
- `POST /api/v1/auth/login` — email/password, sets access + refresh cookies.
- `POST /api/v1/auth/logout` — revoke session, clear cookies.
- `POST /api/v1/auth/refresh` — rotate refresh token, issue new access cookie.
- `POST /api/v1/auth/password/forgot` — password reset request.
- `POST /api/v1/auth/password/reset` — set new password with token.
- `POST /api/v1/auth/password/change` — authenticated change.
- `GET /api/v1/auth/me` — current user profile + memberships.

## Organizations (organizations)
- `GET/POST /api/v1/organizations` — list/create schools (SUPER_ADMIN/SCHOOL_ADMIN scoped).
- `GET/PATCH/DELETE /api/v1/organizations/{id}`
- `GET/POST /api/v1/organizations/{id}/memberships` — membership management.

## Users (users)
- `GET /api/v1/users` — list users (filtered by org).
- `GET/PATCH /api/v1/users/{id}`
- `POST /api/v1/users/{id}/activate`, `POST /api/v1/users/{id}/suspend`.

## Academic structure (academic)
- `academic-years`, `grades`, `classes`, `subjects`, `topics`, `curriculum-versions`, `class-subjects`, `class-enrollments` — full CRUD with org scoping.

## Students (students)
- `GET/POST /api/v1/students`, `GET/PATCH/DELETE /api/v1/students/{id}`
- `GET /api/v1/students/{id}/enrollments`, `GET /api/v1/students/search`

## Teachers (teachers)
- `GET/POST /api/v1/teachers`, `GET/PATCH /api/v1/teachers/{id}`
- `GET /api/v1/teachers/{id}/assignments` (class-subject), `GET /api/v1/teachers/search`

## Parents (parents)
- `GET/POST /api/v1/parents`, `GET/PATCH /api/v1/parents/{id}`
- `POST /api/v1/guardians` — create verified student_guardian relationship.
- `GET /api/v1/parents/{id}/children`

## Gradebook (gradebook)
- `GET/POST /api/v1/assessments`, `GET/PATCH /api/v1/assessments/{id}`
- `GET/POST /api/v1/grades`, `PATCH /api/v1/grades/{id}` (audit record created)
- `GET /api/v1/grades/student/{id}`, `GET /api/v1/grades/class/{id}`, statistics endpoints.

## Homework (homework)
- `GET/POST/PATCH/DELETE /api/v1/assignments`
- `POST /api/v1/assignments/{id}/submissions` (text + files)
- `GET/PATCH /api/v1/submissions/{id}` (teacher feedback/grade)
- `GET /api/v1/submissions` (student view)

## Timetable (timetable)
- `GET/POST/PATCH/DELETE /api/v1/lessons`
- `GET /api/v1/timetable/class/{id}`, `GET /api/v1/timetable/teacher/{id}`
- `POST /api/v1/lessons/{id}/cancel`, replacement handling.

## Attendance (attendance)
- `GET/POST /api/v1/attendance-sessions`
- `POST /api/v1/attendance-sessions/{id}/records` — mark attendance.
- `GET /api/v1/attendance/student/{id}`, `GET /api/v1/attendance/class/{id}` statistics.
- Export endpoint (authorized).

## Learning materials (materials)
- `GET/POST/PATCH/DELETE /api/v1/materials`
- `POST /api/v1/materials/upload` — secure file upload (size/ext/MIME validated).
- `GET /api/v1/materials/{id}/download` — signed/controlled access, private paths not exposed.

## Analytics (analytics)
- `GET /api/v1/analytics/student/{id}`, `GET /api/v1/analytics/teacher/{id}`, `GET /api/v1/analytics/school/{org_id}`
- Real DB aggregations; missing vs zero distinguished.

## Notifications (notifications)
- `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{id}/read`
- `GET/PATCH /api/v1/notification-preferences`

## Rate limiting
- Auth endpoints rate-limited (login, password reset).

## Security notes
- No backend secrets in responses.
- Error messages do not leak internal details.
- File uploads validated server-side (size, extension, MIME magic), stored outside web root or in bucket with private access.
