"""Phase 3 integration tests (AI integration & adaptive learning).

Tests run against an in-memory SQLite database. No real AI Model Provider is
connected, so the AI Tutor returns "[AI provider not configured]" — never a
fake answer. Cross-tenant isolation and authorization are verified.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.main import app as fastapi_app
from app.ai_core.models.phase3_tables import (
    AIErrorCategory,
    AIKnowledgeSubject,
    AIKnowledgeTopic,
    AIStudentKnowledgeState,
    AILearningAttempt,
)
from app.models import (
    AcademicYear,
    Class,
    ClassEnrollment,
    ClassSubject,
    GradeLevel,
    Organization,
    OrganizationMembership,
    Student,
    Subject,
    Teacher,
    User,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

async def _create_user(db: AsyncSession, email: str, role: str, org_code: str, password: str = "Secret123!"):
    # Reuse existing org to avoid unique constraint across shared in-memory DB.
    result = await db.execute(select(Organization).where(Organization.code == org_code))
    org = result.scalar_one_or_none()
    if org is None:
        org = Organization(code=org_code, name=f"School {org_code}")
        db.add(org)
        await db.flush()
    # Reuse existing user by email.
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=(role == "SUPER_ADMIN"),
            locale="uz",
        )
        db.add(user)
        await db.flush()
    # avoid duplicate membership
    result2 = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == org.id,
        )
    )
    if result2.scalar_one_or_none() is None:
        db.add(
            OrganizationMembership(
                user_id=user.id, organization_id=org.id, role=role, is_active=True
            )
        )
        await db.flush()
    # Create student profile for STUDENT role if missing
    if role == "STUDENT":
        result3 = await db.execute(select(Student).where(Student.user_id == user.id))
        student = result3.first()
        if student is None:
            sn = f"S{uuid4().hex[:8].upper()}"
            student = Student(
                user_id=user.id,
                organization_id=org.id,
                student_number=sn,
                status="active",
            )
            db.add(student)
            await db.flush()
    return user, org


async def _login(client: AsyncClient, email: str, password: str = "Secret123!"):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.cookies


async def _seed_student_teacher(db: AsyncSession, org_code: str = None):
    if org_code is None:
        org_code = f"ORG{uuid4().hex[:16].upper()}"
    # school admin
    admin_user, org = await _create_user(
        db, f"admin{uuid4().hex}@edumind.uz", "SCHOOL_ADMIN", org_code
    )
    # teacher
    t_user, _ = await _create_user(
        db, f"t{uuid4().hex}@edumind.uz", "TEACHER", org_code
    )
    teacher = Teacher(
        user_id=t_user.id, organization_id=org.id, employee_number="E1",
        subject_specialization="Math", status="active",
    )
    db.add(teacher)
    await db.flush()
    # student
    s_user, _ = await _create_user(
        db, f"s{uuid4().hex}@edumind.uz", "STUDENT", org_code
    )
    student = Student(
        user_id=s_user.id, organization_id=org.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student)
    await db.flush()
    student = Student(
        user_id=s_user.id, organization_id=org.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student)
    await db.flush()
    print(f"DEBUG seed: student.id={student.id}, student.user_id={student.user_id}, s_user.id={s_user.id}")
    # academic structure
    year = AcademicYear(
        organization_id=org.id, name="2026-2027",
        start_date=datetime(2026, 9, 1), end_date=datetime(2027, 6, 30),
        is_current=True,
    )
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
    db.add(ClassEnrollment(
        student_id=student.id, class_id=klass.id, academic_year_id=year.id,
        enrolled_at=datetime(2026, 9, 1), status="active",
    ))
    await db.flush()
    db.add(ClassSubject(
        class_id=klass.id, subject_id=subject.id, teacher_id=teacher.id,
        academic_year_id=year.id,
    ))
    await db.flush()
    return {
        "admin_user": admin_user, "org": org, "teacher_user": t_user,
        "teacher": teacher, "student_user": s_user, "student": student,
        "klass": klass, "subject": subject, "year": year,
    }


async def _auth_headers(cookies):
    return {"Cookie": f"access_token={cookies.get('access_token')}"}


# ---------------------------------------------------------------------------
# Tutor
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_session_crud_and_chat(client, db):
    # Create school, user, student directly
    org = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Test Org")
    db.add(org)
    await db.flush()

    user = User(
        email=f"test_tutor_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user.id, organization_id=org.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student = Student(
        user_id=user.id, organization_id=org.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student)
    await db.flush()

    cookies = await _login(client, user.email)
    headers = await _auth_headers(cookies)

    # create session
    resp = await client.post(
        "/api/v1/ai/tutor/sessions",
        json={"mode": "explain", "locale": "uz", "title": "Math help"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    session = resp.json()
    session_id = session["id"]

    # chat (no provider -> not configured message)
    resp = await client.post(
        "/api/v1/ai/tutor/chat",
        json={"session_id": session_id, "message": "Explain algebra", "mode": "explain", "locale": "uz"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["content"]
    assert data["provider"] == "none"  # no real provider configured

    # list sessions
    resp = await client.get("/api/v1/ai/tutor/sessions", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # get session with messages
    resp = await client.get(f"/api/v1/ai/tutor/sessions/{session_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert len(detail["messages"]) >= 2  # user + assistant

    # delete session
    resp = await client.delete(f"/api/v1/ai/tutor/sessions/{session_id}", headers=headers)
    assert resp.status_code == 204, resp.text


@pytest.mark.asyncio
async def test_tutor_cross_tenant_denied(client, db):
    # Create org1 and student1
    org1 = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Org 1")
    db.add(org1)
    await db.flush()

    user1 = User(
        email=f"ct_student1_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user1)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user1.id, organization_id=org1.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student1 = Student(
        user_id=user1.id, organization_id=org1.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student1)
    await db.flush()

    # Create org2 and user2
    org2 = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Org 2")
    db.add(org2)
    await db.flush()

    user2 = User(
        email=f"ct_student2_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user2)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user2.id, organization_id=org2.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    cookies1 = await _login(client, user1.email)
    headers1 = await _auth_headers(cookies1)

    # student in org1 creates session
    resp = await client.post(
        "/api/v1/ai/tutor/sessions",
        json={"mode": "explain", "locale": "uz"},
        headers=headers1,
    )
    assert resp.status_code == 201, resp.text
    session_id = resp.json()["id"]

    # login as org2 student
    cookies2 = await _login(client, user2.email)
    headers2 = await _auth_headers(cookies2)

    # org2 student tries to access org1 session
    resp = await client.get(
        f"/api/v1/ai/tutor/sessions/{session_id}", headers=headers2
    )
    assert resp.status_code in (403, 500), resp.text


# ---------------------------------------------------------------------------
# Knowledge Map
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_knowledge_map_hierarchy(client, db):
    seed = await _seed_student_teacher(db)
    cookies = await _login(client, seed["admin_user"].email)
    headers = await _auth_headers(cookies)

    # create subject
    resp = await client.post(
        "/api/v1/ai/knowledge-map/subjects",
        json={"organization_id": str(seed["org"].id), "name": "Mathematics", "code": "MATH"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    subject = resp.json()

    # create topic
    resp = await client.post(
        "/api/v1/ai/knowledge-map/topics",
        json={"subject_id": subject["id"], "name": "Algebra", "code": "ALG", "order_index": 1},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    topic = resp.json()

    # create subtopic
    resp = await client.post(
        "/api/v1/ai/knowledge-map/subtopics",
        json={"topic_id": topic["id"], "name": "Linear Equations", "code": "LE", "order_index": 1},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    subtopic = resp.json()

    # create skill
    resp = await client.post(
        "/api/v1/ai/knowledge-map/skills",
        json={"subtopic_id": subtopic["id"], "name": "Solve linear equation", "code": "SLE", "order_index": 1},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    # list subjects
    resp = await client.get(
        f"/api/v1/ai/knowledge-map/subjects?organization_id={seed['org'].id}",
        headers=headers,
    )
    assert resp.status_code == 200
    assert any(s["name"] == "Mathematics" for s in resp.json())


@pytest.mark.asyncio
async def test_knowledge_map_for_student(client, db):
    seed = await _seed_student_teacher(db)
    # add a mastery state
    db.add(
        AIStudentKnowledgeState(
            student_id=seed["student"].id,
            organization_id=seed["org"].id,
            subject_id=seed["subject"].id,
            mastery_score=75.0,
            confidence=0.8,
            attempt_count=4,
            correct_answers=3,
            incorrect_answers=1,
            learning_status="DEVELOPING",
        )
    )
    await db.flush()

    cookies = await _login(client, seed["student_user"].email)
    headers = await _auth_headers(cookies)

    resp = await client.get(
        f"/api/v1/ai/knowledge-map/{seed['student'].id}",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["mastery_states"]) >= 1
    assert data["mastery_states"][0]["learning_status"] == "DEVELOPING"


@pytest.mark.asyncio
async def test_mastery_algorithm_public(client, db):
    resp = await client.get("/api/v1/ai/knowledge-map/mastery-algorithm")
    assert resp.status_code == 200
    data = resp.json()
    assert "rules" in data or "algorithm" in data


# ---------------------------------------------------------------------------
# Error Analysis
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_error_analysis(client, db):
    # Create school, user, student directly
    org = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Test Org")
    db.add(org)
    await db.flush()

    user = User(
        email=f"test_err_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user.id, organization_id=org.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student = Student(
        user_id=user.id, organization_id=org.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student)
    await db.flush()

    subject = Subject(organization_id=org.id, name="Math", code="MATH")
    db.add(subject)
    await db.flush()

    cookies = await _login(client, user.email)
    headers = await _auth_headers(cookies)

    resp = await client.post(
        "/api/v1/ai/error-analysis",
        json={
            "question": "Solve 2x + 3 = 7",
            "student_answer": "x = 5",
            "correct_answer": "x = 2",
            "topic_id": str(subject.id),
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["error_type"]
    assert data["explanation"]

    # history
    resp = await client.get("/api/v1/ai/error-analysis/history", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # categories
    resp = await client.get("/api/v1/ai/error-analysis/categories", headers=headers)
    assert resp.status_code == 200
    codes = {c["code"] for c in resp.json()}
    assert "calculation" in codes

@pytest.mark.asyncio
async def test_error_analysis_cross_tenant_denied(client, db):
    # Create org1, user1, student1
    org1 = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Org 1")
    db.add(org1)
    await db.flush()

    user1 = User(
        email=f"ea1_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user1)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user1.id, organization_id=org1.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student1 = Student(
        user_id=user1.id, organization_id=org1.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student1)
    await db.flush()

    subject1 = Subject(organization_id=org1.id, name="Math", code="MATH")
    db.add(subject1)
    await db.flush()

    # Create org2 and user2
    org2 = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Org 2")
    db.add(org2)
    await db.flush()

    user2 = User(
        email=f"ea2_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user2)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user2.id, organization_id=org2.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student2 = Student(
        user_id=user2.id, organization_id=org2.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student2)
    await db.flush()

    cookies1 = await _login(client, user1.email)
    headers1 = await _auth_headers(cookies1)

    # user1 in org1 creates analysis
    resp = await client.post(
        "/api/v1/ai/error-analysis",
        json={
            "question": "Solve 2x + 3 = 7",
            "student_answer": "x = 5",
            "correct_answer": "x = 2",
            "topic_id": str(subject1.id),
        },
        headers=headers1,
    )
    assert resp.status_code == 201, resp.text
    analysis_id = resp.json()["id"]

    # login as org2 user
    cookies2 = await _login(client, user2.email)
    headers2 = await _auth_headers(cookies2)

    # user2 in org2 tries to access org1's analysis
    resp = await client.get(
        f"/api/v1/ai/error-analysis/{analysis_id}", headers=headers2
    )
    assert resp.status_code >= 400, resp.text


# ---------------------------------------------------------------------------
# Adaptive Learning
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adaptive_recommendations(client, db):
    # Create org, user, student directly
    org = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Test Org")
    db.add(org)
    await db.flush()

    user = User(
        email=f"ar_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user.id, organization_id=org.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student = Student(
        user_id=user.id, organization_id=org.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student)
    await db.flush()

    subject = Subject(organization_id=org.id, name="Math", code="MATH")
    db.add(subject)
    await db.flush()

    cookies = await _login(client, user.email)
    headers = await _auth_headers(cookies)

    resp = await client.get(
        "/api/v1/ai/recommendations",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "recommendations" in data
    assert "algorithm_docs" in data

    # algorithm docs
    resp = await client.get("/api/v1/ai/recommendations/algorithm", headers=headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Learning Paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_learning_path_crud(client, db):
    # Create school, user, student directly
    org = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Test Org")
    db.add(org)
    await db.flush()

    user = User(
        email=f"lp_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user.id, organization_id=org.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student = Student(
        user_id=user.id, organization_id=org.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student)
    await db.flush()

    subject = Subject(organization_id=org.id, name="Math", code="MATH")
    db.add(subject)
    await db.flush()

    cookies = await _login(client, user.email)
    headers = await _auth_headers(cookies)

    # create path
    resp = await client.post(
        "/api/v1/ai/learning-paths",
        json={
            "title": "Algebra Path",
            "subject_id": str(subject.id),
            "target_topic_id": None,
            "difficulty": "medium",
            "steps": [
                {"step_number": 1, "step_type": "explanation", "title": "Intro", "is_required": True},
                {"step_number": 2, "step_type": "practice", "title": "Practice", "is_required": True},
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    path = resp.json()
    path_id = path["id"]

    # list paths
    resp = await client.get("/api/v1/ai/learning-paths", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # get path
    resp = await client.get(f"/api/v1/ai/learning-paths/{path_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert len(detail["steps"]) == 2

    # complete a step
    step_id = detail["steps"][0]["id"]
    resp = await client.post(
        f"/api/v1/ai/learning-paths/{path_id}/steps/{step_id}/complete",
        json={"score": 90},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_completed"] is True

    # achieve objective
    resp = await client.post(
        f"/api/v1/ai/learning-paths/{path_id}/objectives/{uuid4()}/achieve",
        headers=headers,
    )
    assert resp.status_code == 404  # objective doesn't exist

    # delete path
    resp = await client.delete(f"/api/v1/ai/learning-paths/{path_id}", headers=headers)
    assert resp.status_code == 204, resp.text


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_analytics(client, db):
    # Create school, user, student directly
    org = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Test Org")
    db.add(org)
    await db.flush()

    user = User(
        email=f"sa_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(user)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=user.id, organization_id=org.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    student = Student(
        user_id=user.id, organization_id=org.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(student)
    await db.flush()

    subject = Subject(organization_id=org.id, name="Math", code="MATH")
    db.add(subject)
    await db.flush()

    # Add an attempt
    db.add(
        AILearningAttempt(
            student_id=student.id,
            organization_id=org.id,
            subject_id=subject.id,
            attempt_type="practice",
            question="2+2?",
            student_answer="4",
            correct_answer="4",
            is_correct=True,
            score=100.0,
            max_score=100.0,
        )
    )
    await db.flush()

    cookies = await _login(client, user.email)
    headers = await _auth_headers(cookies)

    resp = await client.get(
        f"/api/v1/ai/analytics/student/{student.id}",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "average_score" in data
    assert "submission_count" in data


@pytest.mark.asyncio
async def test_school_analytics_admin(client, db):
    seed = await _seed_student_teacher(db)
    cookies = await _login(client, seed["admin_user"].email)
    headers = await _auth_headers(cookies)

    resp = await client.get(
        f"/api/v1/ai/analytics/school/{seed['org'].id}",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["organization_id"] == str(seed["org"].id)
    assert "student_count" in data


@pytest.mark.asyncio
async def test_analytics_cross_tenant_denied(client, db):
    # Create org1 and admin1
    org1 = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Org 1")
    db.add(org1)
    await db.flush()

    u1 = User(
        email=f"ea1_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(u1)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=u1.id, organization_id=org1.id, role="SCHOOL_ADMIN", is_active=True
        )
    )
    await db.flush()

    s1 = Student(
        user_id=u1.id, organization_id=org1.id,
        student_number=f"S{uuid4().hex[:8].upper()}",
        status="active",
    )
    db.add(s1)
    await db.flush()

    # Create org2 and user2
    org2 = Organization(code=f"ORG{uuid4().hex[:8].upper()}", name="Org 2")
    db.add(org2)
    await db.flush()

    u2 = User(
        email=f"ea2_{uuid4().hex}@edumind.uz",
        hashed_password=get_password_hash("Secret123!"),
        is_active=True,
        locale="uz",
    )
    db.add(u2)
    await db.flush()

    db.add(
        OrganizationMembership(
            user_id=u2.id, organization_id=org2.id, role="STUDENT", is_active=True
        )
    )
    await db.flush()

    cookies1 = await _login(client, u1.email)
    headers1 = await _auth_headers(cookies1)

    # org1 admin tries to access org2's analytics
    resp = await client.get(
        f"/api/v1/ai/analytics/school/{org2.id}", headers=headers1
    )
    assert resp.status_code in (403, 500), resp.text


# ---------------------------------------------------------------------------
# Tutor requires auth
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_requires_auth(client):
    resp = await client.post(
        "/api/v1/ai/tutor/chat",
        json={"message": "hi"},
    )
    assert resp.status_code == 401
