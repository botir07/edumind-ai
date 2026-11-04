"""Access Control tests (run with pytest)."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.access_control.roles import ROLE_MAX_TOP_K
from app.ai_core.access_control.tenant_scope import is_member_of, resolve_organization_scope, user_org_ids


class FakeSession:
    """Stub session returning membership rows for a given user_id.

    _return_col: 'org' -> return (organization_id,); 'role' -> return (role,).
    Tests set _expected_user_id and _return_col before calling.
    """
    def __init__(self, memberships):
        self.memberships = memberships
        self._expected_user_id = None
        self._return_col = "org"

    async def execute(self, stmt):
        user_id = self._expected_user_id
        rows = [
            (m["organization_id"], m["role"])
            for m in self.memberships
            if m["user_id"] == user_id and m["is_active"]
        ]
        return FakeResult(rows)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows
    def all(self):
        return self._rows
    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


@pytest.mark.asyncio
async def test_resolve_organization_scope_filters_by_membership():
    session = FakeSession([
        {"user_id": "u1", "organization_id": "org-a", "role": "TEACHER", "is_active": True},
        {"user_id": "u1", "organization_id": "org-b", "role": "STUDENT", "is_active": True},
        {"user_id": "u2", "organization_id": "org-a", "role": "PARENT", "is_active": True},
        {"user_id": "u1", "organization_id": "org-c", "role": "STUDENT", "is_active": False},
    ])
    session._expected_user_id = "u1"
    ids = await resolve_organization_scope(session, "u1")
    assert set(ids) == {"org-a", "org-b"}, ids
    session._expected_user_id = "u2"
    ids2 = await resolve_organization_scope(session, "u2")
    assert ids2 == ["org-a"], ids2
    # requested org not in membership -> empty
    session._expected_user_id = "u1"
    ids3 = await resolve_organization_scope(session, "u1", requested_org_id="org-z")
    assert ids3 == [], ids3
    # requested org in membership -> single
    ids4 = await resolve_organization_scope(session, "u1", requested_org_id="org-b")
    assert ids4 == ["org-b"], ids4
    print("tenant scope OK")


@pytest.mark.asyncio
async def test_is_member_of():
    session = FakeSession([
        {"user_id": "u1", "organization_id": "org-a", "role": "TEACHER", "is_active": True},
    ])
    session._expected_user_id = "u1"
    assert await is_member_of(session, "u1", "org-a") is True
    assert await is_member_of(session, "u1", "org-b") is False
    print("is_member_of OK")


@pytest.mark.asyncio
async def test_enforcer_tool_permissions():
    session = FakeSession([
        {"user_id": "u1", "organization_id": "org-a", "role": "STUDENT", "is_active": True},
    ])
    session._expected_user_id = "u1"
    enforcer = AICoreEnforcer(session=session, user_id="u1")
    assert await enforcer.may_execute_tool("student") is True
    assert await enforcer.may_execute_tool("school_admin") is False

    session2 = FakeSession([
        {"user_id": "u2", "organization_id": "org-a", "role": "SUPER_ADMIN", "is_active": True},
    ])
    session2._expected_user_id = "u2"
    enforcer2 = AICoreEnforcer(session=session2, user_id="u2")
    for cat in ["student", "teacher", "parent", "school_admin", "platform"]:
        assert await enforcer2.may_execute_tool(cat) is True
    print("tool permissions OK")


@pytest.mark.asyncio
async def test_enforcer_org_isolation():
    session = FakeSession([
        {"user_id": "u1", "organization_id": "org-a", "role": "TEACHER", "is_active": True},
    ])
    session._expected_user_id = "u1"
    enforcer = AICoreEnforcer(session=session, user_id="u1")
    assert await enforcer.can_access_org("org-a") is True
    assert await enforcer.can_access_org("org-b") is False
    print("org isolation OK")


@pytest.mark.asyncio
async def test_max_top_k():
    session = FakeSession([
        {"user_id": "u1", "organization_id": "org-a", "role": "STUDENT", "is_active": True},
    ])
    session._expected_user_id = "u1"
    enforcer = AICoreEnforcer(session=session, user_id="u1")
    assert await enforcer.max_top_k() == ROLE_MAX_TOP_K["STUDENT"]

    session2 = FakeSession([
        {"user_id": "u2", "organization_id": "org-a", "role": "SUPER_ADMIN", "is_active": True},
    ])
    session2._expected_user_id = "u2"
    enforcer2 = AICoreEnforcer(session=session2, user_id="u2")
    assert await enforcer2.max_top_k() == ROLE_MAX_TOP_K["SUPER_ADMIN"]
    print("max_top_k OK")


if __name__ == "__main__":
    asyncio.run(test_resolve_organization_scope_filters_by_membership())
    asyncio.run(test_is_member_of())
    asyncio.run(test_enforcer_tool_permissions())
    asyncio.run(test_enforcer_org_isolation())
    asyncio.run(test_max_top_k())
    print("ALL ACCESS CONTROL TESTS OK")
