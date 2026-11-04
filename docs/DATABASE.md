# Database — EduMind AI

## Engine
PostgreSQL, accessed via SQLAlchemy 2.x async (asyncpg driver). Alembic for migrations.

## Conventions
- UUID primary keys (`uuid_generate_v4()` / `uuid4`).
- `created_at`, `updated_at` (timestamptz, server default `now()`) on every entity.
- Foreign keys with `ON DELETE` rules (CASCADE/SET NULL as appropriate).
- Unique constraints, check constraints, appropriate indexes.
- `organization_id` on all org-owned tables for tenant isolation.
- Soft deletes (`deleted_at`) where policy requires archive rather than hard delete.

## Core tables
1. `organizations` — schools (id, name, code, legal_name, address, phone, email, timezone, is_active, settings, created_at, updated_at)
2. `users` — platform users (id, email, username, hashed_password, full_name, phone, is_active, is_superuser, email_verified, created_at, updated_at)
3. `organization_memberships` — (id, user_id, organization_id, role, is_active, joined_at, created_at) — unique(user_id, organization_id)
4. `user_sessions` — refresh token sessions (id, user_id, refresh_token_hash, expires_at, revoked_at, user_agent, ip, created_at)
5. `audit_logs` — (id, actor_user_id, organization_id, action, target_type, target_id, details, ip, user_agent, created_at)
6. `consent_records` — GDPR/local-law consent (id, user_id, purpose, granted, granted_at, withdrawn_at)

## Academic structure
7. `academic_years` — (id, organization_id, name, start_date, end_date, is_current, created_at, updated_at)
8. `grades` (grade levels) — (id, organization_id, name, level_order, created_at, updated_at)
9. `classes` — (id, organization_id, grade_id, name, room_teacher_id, capacity, created_at, updated_at)
10. `subjects` — (id, organization_id, name, code, created_at, updated_at)
11. `topics` — (id, subject_id, name, order_index, created_at, updated_at)
12. `curriculum_versions` — (id, organization_id, academic_year_id, name, is_active, created_at, updated_at)
13. `class_subjects` — (id, class_id, subject_id, teacher_id, academic_year_id) — unique(class_id, subject_id, academic_year_id)
14. `class_enrollments` — (id, student_id, class_id, academic_year_id, enrolled_at, status) — unique(student_id, class_id, academic_year_id)

## People
15. `students` — (id, user_id, organization_id, student_number, date_of_birth, gender, address, status, created_at, updated_at) — unique(student_number, organization_id)
16. `teachers` — (id, user_id, organization_id, employee_number, subject_specialization, hire_date, status, created_at, updated_at) — unique(employee_number, organization_id)
17. `parents` — (id, user_id, organization_id, created_at, updated_at)
18. `student_guardians` — (id, student_id, parent_id, relationship, is_verified, verified_by, verified_at, created_at) — unique(student_id, parent_id)

## Gradebook
19. `assessments` — (id, class_subject_id, title, category, max_score, weight, date_assigned, due_date, academic_year_id, created_at, updated_at)
20. `grades` (grade records) — (id, assessment_id, student_id, score, comment, entered_by, entered_at, updated_at)
21. `grade_history` — audit of grade changes (id, grade_id, old_score, new_score, changed_by, reason, created_at)

## Homework
22. `assignments` — (id, class_id, subject_id, teacher_id, title, description, deadline, max_score, academic_year_id, created_at, updated_at)
23. `assignment_submissions` — (id, assignment_id, student_id, text_answer, status, submitted_at, graded_at, feedback, grade, graded_by)
24. `submission_files` — (id, submission_id, filename, storage_path, mime_type, size, uploaded_at)

## Timetable
25. `rooms` — (id, organization_id, name, capacity, created_at, updated_at)
26. `lessons` — (id, class_id, subject_id, teacher_id, room_id, day_of_week, start_time, end_time, academic_year_id, is_cancelled, replacement_teacher_id, created_at, updated_at)

## Attendance
27. `attendance_sessions` — (id, class_id, subject_id, teacher_id, date, academic_year_id, created_at, updated_at)
28. `attendance_records` — (id, session_id, student_id, status, marked_by, marked_at, note)

## Learning materials
29. `learning_materials` — (id, organization_id, subject_id, topic_id, class_id, grade_id, title, type, language, author_id, file_path, mime_type, size, external_url, is_published, created_at, updated_at)

## Notifications
30. `notifications` — (id, organization_id, recipient_user_id, title, body, type, read_at, created_at)
31. `notification_preferences` — (id, user_id, channel, enabled, created_at, updated_at)

## Indexes (selected)
- `organization_memberships(user_id)`, `(organization_id)`
- `classes(organization_id, grade_id)`, `class_enrollments(student_id, class_id, academic_year_id)`
- `students(organization_id, student_number)`, `teachers(organization_id, employee_number)`
- `assessments(class_subject_id)`, `grades(assessment_id, student_id)`
- `assignments(class_id, teacher_id)`, `assignment_submissions(assignment_id, student_id)`
- `lessons(class_id, day_of_week)`, `attendance_records(session_id, student_id)`
- `learning_materials(organization_id, subject_id, is_published)`
- `audit_logs(organization_id, created_at)`, `notifications(recipient_user_id)`

## Constraints (selected)
- `grades.score >= 0 AND grades.score <= assessments.max_score` (enforced via check + application validation)
- `attendance_records.status IN ('present','absent','late','excused')`
- `lessons.start_time < lessons.end_time`
- `organization_memberships.role IN ('SUPER_ADMIN','SCHOOL_ADMIN','TEACHER','STUDENT','PARENT')`

## Migrations
- Alembic (`alembic.ini`, `env.py` targeting SQLAlchemy metadata).
- Migration files generated with `alembic revision --autogenerate`.
- No destructive migrations against existing user data.
- Seed data only for development/testing (clearly marked dev accounts, fictional students).

## Transaction management
- Async session scoped per request; services commit/rollback explicitly; FastAPI dependency closes session.
- Audit writes within the same transaction as the business change.
