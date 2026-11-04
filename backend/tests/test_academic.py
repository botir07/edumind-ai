"""Academic structure integration tests."""
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.models.user import User


async def _school_admin(db: AsyncSession, email: str = "admin@edumind.uz"):
    u = User(email=email, hashed_password=get_password_hash("Secret123!"), is_active=True, is_superuser=False)
    db.add(u)
    await db.flush()
    org = Organization(name="School", code="SCH-A")
    db.add(org)
    await db.flush()
    db.add(OrganizationMembership(user_id=u.id, organization_id=org.id, role="SCHOOL_ADMIN", is_active=True))
    await db.flush()
    return u, org


@pytest.mark.asyncio
async def test_academic_crud_flow(client, db):
    user, org = await _school_admin(db)
    resp = await client.post("/api/v1/auth/login", json={"email": "admin@edumind.uz", "password": "Secret123!"})
    assert resp.status_code == 200
    cookies = resp.cookies

    # create academic year
    resp = await client.post(
        "/api/v1/academic/academic-years",
        json={"name": "2026-2027", "start_date": "2026-09-01", "end_date": "2027-06-30", "is_current": True},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    year = resp.json()
    assert year["organization_id"] == str(org.id)
    year_id = year["id"]

    # list academic years for org
    resp = await client.get(f"/api/v1/academic/academic-years?organization_id={org.id}", cookies=cookies)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # create grade level
    resp = await client.post(
        "/api/v1/academic/grade-levels",
        json={"name": "5th Grade", "level_order": 5, "organization_id": str(org.id)},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    grade = resp.json()
    grade_id = grade["id"]

    # create class
    resp = await client.post(
        "/api/v1/academic/classes",
        json={"name": "5-A", "grade_id": grade_id, "organization_id": str(org.id)},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    klass = resp.json()
    class_id = klass["id"]

    # create subject
    resp = await client.post(
        "/api/v1/academic/subjects",
        json={"name": "Mathematics", "code": "MATH", "organization_id": str(org.id)},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    subject = resp.json()

    # create topic
    resp = await client.post(
        "/api/v1/academic/topics",
        json={"subject_id": subject["id"], "name": "Algebra", "order_index": 1},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text

    # list topics for subject
    resp = await client.get(f"/api/v1/academic/topics?subject_id={subject['id']}", cookies=cookies)
    assert resp.status_code == 200
    assert any(t["name"] == "Algebra" for t in resp.json())

    # org isolation: different org id returns empty for this school admin
    resp = await client.get(
        "/api/v1/academic/academic-years?organization_id=00000000-0000-0000-0000-000000000000",
        cookies=cookies,
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_academic_requires_auth(client):
    resp = await client.get("/api/v1/academic/subjects")
    assert resp.status_code == 401
