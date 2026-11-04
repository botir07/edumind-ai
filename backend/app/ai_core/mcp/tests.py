"""MCP tests (run with pytest)."""
import asyncio
import pytest

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.mcp.server import MCPServer
from app.ai_core.mcp.schemas import ToolCall
from app.ai_core.mcp.registry import registry


class FakeSession:
    def __init__(self, memberships):
        self.memberships = memberships
        self._expected_user_id = None
    async def execute(self, stmt):
        user_id = self._expected_user_id
        rows = [(m["organization_id"], m["role"]) for m in self.memberships if m["user_id"] == user_id and m["is_active"]]
        class R:
            def __init__(self, rows): self._rows = rows
            def all(self): return self._rows
        return R(rows)


@pytest.mark.asyncio
async def test_mcp_list_tools_role_scoped():
    # register happens in tools module import; just check registry
    student_tools = registry.list_tools(role="STUDENT")
    names = {t.name for t in student_tools}
    assert "get_my_grades" in names
    assert "get_school_statistics" not in names  # school_admin only
    teacher_tools = registry.list_tools(role="TEACHER")
    tnames = {t.name for t in teacher_tools}
    assert "get_class_students" in tnames
    assert "get_school_statistics" not in tnames
    print("MCP role scoping OK")


@pytest.mark.asyncio
async def test_mcp_execution_permissions():
    session = FakeSession([
        {"user_id": "u1", "organization_id": "org-a", "role": "STUDENT", "is_active": True},
    ])
    session._expected_user_id = "u1"
    enforcer = AICoreEnforcer(session=session, user_id="u1")
    server = MCPServer(enforcer)

    # student can call get_my_grades
    res = await server.call_tool(ToolCall(name="get_my_grades", arguments={}, user_id="u1", organization_id="org-a"))
    assert res.success is True, res.error
    # student cannot call school_admin tool
    res2 = await server.call_tool(ToolCall(name="get_school_statistics", arguments={}, user_id="u1", organization_id="org-a"))
    assert res2.success is False
    assert res2.error_code == "insufficient_role"
    # unknown tool
    res3 = await server.call_tool(ToolCall(name="nonexistent_tool", arguments={}, user_id="u1", organization_id="org-a"))
    assert res3.success is False
    assert res3.error_code == "tool_not_found"
    # missing required argument (get_my_profile is a student tool requiring user_id)
    res4 = await server.call_tool(ToolCall(name="get_my_profile", arguments={}, user_id="u1", organization_id="org-a"))
    assert res4.success is False
    assert res4.error_code == "missing_argument"
    print("MCP execution permissions OK")


@pytest.mark.asyncio
async def test_mcp_no_arbitrary_access():
    # student calling child tools (parent-only) should fail
    session = FakeSession([
        {"user_id": "u1", "organization_id": "org-a", "role": "STUDENT", "is_active": True},
    ])
    session._expected_user_id = "u1"
    enforcer = AICoreEnforcer(session=session, user_id="u1")
    server = MCPServer(enforcer)
    res = await server.call_tool(ToolCall(name="get_child_grades", arguments={"child_id": "c1"}, user_id="u1", organization_id="org-a"))
    assert res.success is False
    assert res.error_code == "insufficient_role"
    print("MCP no cross-role access OK")


if __name__ == "__main__":
    asyncio.run(test_mcp_list_tools_role_scoped())
    asyncio.run(test_mcp_execution_permissions())
    asyncio.run(test_mcp_no_arbitrary_access())
    print("ALL MCP TESTS OK")
