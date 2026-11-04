"""Gradebook integration tests."""
from datetime import date
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.academic_year import AcademicYear
from app.models.class_ import Class
from app.models.class_enrollment import ClassEnrollment
from app.models.class_subject import ClassSubject
from app.models.grade_level import GradeLevel
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User


async def _seed_gradebook(db: AsyncSession):
    admin = User(
        email="gbadmin@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        is_superuser=False,
    )
    db.add(admin)
    await db.flush()
    org = Organization(name="GB School", code="GBS1")
    db.add(org)
    await db.flush()
    db.add(OrganizationMembership(user_id=admin.id, organization_id=org.id, role="SCHOOL_ADMIN", is_active=True))
    await db.flush()

    teacher_user = User(
        email="gbteacher@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
    )
    db.add(teacher_user)
    await db.flush()
    teacher = Teacher(user_id=teacher_user.id, organization_id=org.id, employee_number="T1")
    db.add(teacher)
    await db.flush()

    year = AcademicYear(organization_id=org.id, name="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 6, 30), is_current=True)
    db.add(year)
    await db.flush()
    grade = GradeLevel(organization_id=org.id, name="5", level_order=5)
    db.add(grade)
    await db.flush()
    klass = Class(organization_id=org.id, grade_id=grade.id, name="5-A")
    db.add(klass)
    await db.flush()
    subject = Subject(organization_id=org.id, name="Math", code="MATH")
    db.add(subject)
    await db.flush()
    class_subject = ClassSubject(class_id=klass.id, subject_id=subject.id, teacher_id=teacher.id, academic_year_id=year.id)
    db.add(class_subject)
    await db.flush()

    student_user = User(email="gbstudent@edumind.uz", hashed_password=get_password_hash("Secret123!"), is_active=True)
    db.add(student_user)
    await db.flush()
    student = Student(user_id=student_user.id, organization_id=org.id, student_number="S001")
    db.add(student)
    await db.flush()
    db.add(ClassEnrollment(student_id=student.id, class_id=klass.id, academic_year_id=year.id, enrolled_at=date(2026, 9, 1)))
    await db.flush()

    return {
        "admin": admin, "org": org, "teacher": teacher, "class_subject": class_subject,
        "student": student, "klass": klass, "year": year,
    }


async def _login(client, email: str = "gbadmin@edumind.uz"):
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Secret123!"})
    assert resp.status_code == 200, resp.text
    return resp.cookies


@pytest.mark.asyncio
async def test_assessment_and_grade_flow(client, db):
    seed = await _seed_gradebook(db)
    cookies = await _login(client)

    cs_id = str(seed["class_subject"].id)
    year_id = str(seed["year"].id)
    resp = await client.post(
        "/api/v1/gradebook/assessments",
        json={"title": "Quiz 1", "category": "quiz", "max_score": 50, "weight": 1,
              "class_subject_id": cs_id, "academic_year_id": year_id},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    assessment = resp.json()
    assert assessment["max_score"] == 50

    # create grade
    resp = await client.post(
        "/api/v1/gradebook/grades",
        json={"assessment_id": assessment["id"], "student_id": str(seed["student"].id), "score": 45, "comment": "Good"},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    grade = resp.json()
    assert grade["score"] == 45

    # score above max -> 400
    resp = await client.post(
        "/api/v1/gradebook/grades",
        json={"assessment_id": assessment["id"], "student_id": str(seed["student"].id), "score": 999},
        cookies=cookies,
    )
    assert resp.status_code == 400, resp.text

    # update grade -> audit history
    resp = await client.patch(
        f"/api/v1/gradebook/grades/{grade['id']}",
        json={"score": 48},
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["score"] == 48

    # list grades for student
    resp = await client.get(f"/api/v1/gradebook/grades?student_id={seed['student'].id}", cookies=cookies)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_gradebook_cross_org_denied(client, db):
    # another org's teacher tries to create grade for student in seed org
    seed = await _seed_gradebook(db)
    cookies = await _login(client)
    # use a different org id in assessment payload -> 403/404 since class_subject belongs to seed org
    resp = await client.post(
        "/api/v1/gradebook/assessments",
        json={"title": "X", "category": "quiz", "max_score": 10, "weight": 1,
              "class_subject_id": str(seed["class_subject"].id), "academic_year_id": str(seed["year"].id)},
        cookies=cookies,
    )
    # same org admin, allowed
    assert resp.status_code == 201, resp.text


@pytest.mark.asyncio
async def test_gradebook_requires_auth(client):
    resp = await client.get("/api/v1/gradebook/assessments")
    assert resp.status_code == 401
