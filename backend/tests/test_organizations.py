"""Organizations integration tests."""
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.models.user import User


async def _superuser(db: AsyncSession, email: str = "super@edumind.uz"):
    u = User(email=email, hashed_password=get_password_hash("Secret123!"), is_active=True, is_superuser=True)
    db.add(u)
    await db.flush()
    return u


@pytest.mark.asyncio
async def test_create_and_list_organization(client, db):
    await _superuser(db)
    # login as superuser
    resp = await client.post("/api/v1/auth/login", json={"email": "super@edumind.uz", "password": "Secret123!"})
    assert resp.status_code == 200
    cookies = resp.cookies

    resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Test School", "code": "SCH001", "timezone": "Asia/Tashkent"},
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    org = resp.json()
    assert org["code"] == "SCH001"
    assert org["name"] == "Test School"

    # duplicate code
    resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Dup", "code": "SCH001"},
        cookies=cookies,
    )
    assert resp.status_code == 409, resp.text

    # list
    resp = await client.get("/api/v1/organizations", cookies=cookies)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] >= 1
    assert any(o["code"] == "SCH001" for o in body["data"])


@pytest.mark.asyncio
async def test_organization_isolation_for_member(client, db):
    # non-superuser member of a different org should not create/see others' orgs as admin
    su = await _superuser(db, email="su2@edumind.uz")
    org_a = Organization(name="Org A", code="ORGA")
    db.add(org_a)
    await db.flush()
    org_b = Organization(name="Org B", code="ORGB")
    db.add(org_b)
    await db.flush()
    member = User(email="member@edumind.uz", hashed_password=get_password_hash("Secret123!"), is_active=True)
    db.add(member)
    await db.flush()
    db.add(OrganizationMembership(user_id=member.id, organization_id=org_a.id, role="TEACHER", is_active=True))
    await db.flush()

    resp = await client.post("/api/v1/auth/login", json={"email": "member@edumind.uz", "password": "Secret123!"})
    assert resp.status_code == 200
    cookies = resp.cookies

    # member cannot create an organization (not SUPER_ADMIN/SCHOOL_ADMIN)
    resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org C", "code": "ORGC"},
        cookies=cookies,
    )
    assert resp.status_code == 403, resp.text

    # member can see org_a via list (filtered)
    resp = await client.get("/api/v1/organizations", cookies=cookies)
    assert resp.status_code == 200
    codes = {o["code"] for o in resp.json()["data"]}
    assert "ORGA" in codes
    assert "ORGB" not in codes


@pytest.mark.asyncio
async def test_get_and_update_organization(client, db):
    su = await _superuser(db, email="su3@edumind.uz")
    org = Organization(name="Old", code="OLD1")
    db.add(org)
    await db.flush()
    db.add(OrganizationMembership(user_id=su.id, organization_id=org.id, role="SUPER_ADMIN", is_active=True))
    await db.flush()

    resp = await client.post("/api/v1/auth/login", json={"email": "su3@edumind.uz", "password": "Secret123!"})
    cookies = resp.cookies

    resp = await client.get(f"/api/v1/organizations/{org.id}", cookies=cookies)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Old"

    resp = await client.patch(
        f"/api/v1/organizations/{org.id}",
        json={"name": "New Name"},
        cookies=cookies,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
