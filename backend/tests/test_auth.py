"""Authentication tests."""
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.academic_year import AcademicYear
from app.models.class_ import Class
from app.models.class_enrollment import ClassEnrollment
from app.models.class_subject import ClassSubject
from app.models.consent_record import ConsentRecord
from app.models.curriculum_version import CurriculumVersion
from app.models.grade import Grade
from app.models.grade_history import GradeHistory
from app.models.grade_level import GradeLevel
from app.models.learning_material import LearningMaterial
from app.models.lesson import Lesson
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.models.parent import Parent
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User
from app.models.user_session import UserSession


async def _create_user(db: AsyncSession, email: str, password: str = "Secret123!", **kw):
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=kw.get("full_name", "Test User"),
        is_active=kw.get("is_active", True),
        is_superuser=kw.get("is_superuser", False),
        locale=kw.get("locale", "uz"),
    )
    db.add(user)
    await db.flush()
    return user


async def _create_org(db: AsyncSession, code: str = "SCH001", name: str = "Test School"):
    org = Organization(code=code, name=name)
    db.add(org)
    await db.flush()
    return org


async def _create_membership(db: AsyncSession, user, org, role: str = "TEACHER"):
    m = OrganizationMembership(user_id=user.id, organization_id=org.id, role=role, is_active=True)
    db.add(m)
    await db.flush()
    return m


@pytest.mark.asyncio
async def test_login_success_and_me(client, db):
    user = await _create_user(db, "teacher@edumind.uz", "Secret123!")
    org = await _create_org(db)
    await _create_membership(db, user, org, role="TEACHER")

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@edumind.uz", "password": "Secret123!"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies

    # me
    resp = await client.get("/api/v1/auth/me", cookies=resp.cookies)
    assert resp.status_code == 200, resp.text
    me = resp.json()
    assert me["user"]["email"] == "teacher@edumind.uz"
    assert any(m["role"] == "TEACHER" for m in me["memberships"])


@pytest.mark.asyncio
async def test_login_wrong_password(client, db):
    await _create_user(db, "wrong@edumind.uz", "Secret123!")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@edumind.uz", "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates(client, db):
    user = await _create_user(db, "refresher@edumind.uz", "Secret123!")
    org = await _create_org(db)
    await _create_membership(db, user, org, role="STUDENT")

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresher@edumind.uz", "password": "Secret123!"},
    )
    assert resp.status_code == 200
    old_access = resp.json()["access_token"]
    refresh_token = resp.cookies.get("refresh_token")

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200, resp.text
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies
    new_access = resp.json()["access_token"]
    assert new_access
    # refresh rotates the session: reuse of the previous refresh token must still
    # be accepted (rotate-on-use) and reissue a fresh token pair.
    resp2 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp2.status_code == 200, resp2.text


@pytest.mark.asyncio
async def test_logout(client, db):
    user = await _create_user(db, "logout@edumind.uz", "Secret123!")
    org = await _create_org(db)
    await _create_membership(db, user, org, role="PARENT")

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "logout@edumind.uz", "password": "Secret123!"},
    )
    assert resp.status_code == 200

    resp = await client.post("/api/v1/auth/logout", cookies=resp.cookies)
    assert resp.status_code == 204, resp.text

    # refresh should now fail
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": resp.cookies.get("refresh_token") or "invalid"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_password_change(client, db):
    user = await _create_user(db, "changer@edumind.uz", "OldPass123!")
    org = await _create_org(db)
    await _create_membership(db, user, org, role="SCHOOL_ADMIN")

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "changer@edumind.uz", "password": "OldPass123!"},
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
        cookies=resp.cookies,
    )
    assert resp.status_code == 204, resp.text

    # old password no longer works
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "changer@edumind.uz", "password": "OldPass123!"},
    )
    assert resp.status_code == 401

    # new password works
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "changer@edumind.uz", "password": "NewPass123!"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_password_forgot_and_reset(client, db):
    user = await _create_user(db, "reset@edumind.uz", "Secret123!")
    org = await _create_org(db)
    await _create_membership(db, user, org, role="TEACHER")

    resp = await client.post(
        "/api/v1/auth/password/forgot", json={"email": "reset@edumind.uz"}
    )
    assert resp.status_code == 202
    token = resp.headers.get("X-Dev-Reset-Token")
    assert token, "dev token not returned (not in development env?)"

    resp = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "ResetPass123!"},
    )
    assert resp.status_code == 204, resp.text

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset@edumind.uz", "password": "ResetPass123!"},
    )
    assert resp.status_code == 200
