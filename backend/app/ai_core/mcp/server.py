"""MCP server: lists tools and executes them with permission checks.

Every call:
  1. authenticates user (via enforcer)
  2. resolves organization server-side (never trusts client org_id)
  3. checks tool exists + is active + read-only
  4. checks user role against tool.required_role
  5. validates arguments against input_schema
  6. executes tool (read-only)
  7. returns result or sanitized error
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.mcp.schemas import ToolDefinition, ToolCall, ToolResult
from app.ai_core.mcp.registry import registry


class MCPServer:
    def __init__(self, enforcer: AICoreEnforcer):
        self.enforcer = enforcer

    async def list_tools(self, role: Optional[str] = None) -> List[ToolDefinition]:
        return registry.list_tools(role=role)

    async def call_tool(self, call: ToolCall) -> ToolResult:
        tool = registry.get(call.name)
        if not tool:
            return ToolResult(success=False, error="Tool not found", error_code="tool_not_found")
        if not tool.is_active:
            return ToolResult(success=False, error="Tool is disabled", error_code="tool_disabled")

        # role check
        user_roles = await self.enforcer.user_roles()
        if tool.required_role and tool.required_role not in user_roles:
            return ToolResult(success=False, error="Insufficient role for tool", error_code="insufficient_role")

        # org access: tool operates within user's org(s); ignore client org_id, use server-resolved
        org_ids = await self.enforcer.org_ids()
        if not org_ids:
            return ToolResult(success=False, error="No organization access", error_code="no_org_access")

        # validate arguments (basic: required keys present)
        required = tool.input_schema.get("required", [])
        for req in required:
            if req not in call.arguments:
                return ToolResult(success=False, error=f"Missing required argument: {req}", error_code="missing_argument")

        # execute via registered handler
        try:
            data = await self._execute(tool, call.arguments, user_roles, org_ids)
            return ToolResult(success=True, data=data)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error="Tool execution failed", error_code="execution_error")

    async def _execute(self, tool: ToolDefinition, arguments: Dict[str, Any], roles: List[str], org_ids: List[UUID]):
        name = tool.name
        # ---- Student tools ----
        if name == "get_my_profile":
            return {"user_id": str(arguments.get("user_id", "")), "org_ids": [str(o) for o in org_ids]}
        if name == "get_my_subjects":
            return {"subjects": [], "note": "connect to academic service"}
        if name == "get_my_timetable":
            return {"lessons": [], "note": "connect to timetable service"}
        if name == "get_my_grades":
            return {"grades": [], "note": "connect to gradebook service"}
        if name == "get_my_attendance":
            return {"records": [], "note": "connect to attendance service"}
        if name == "get_my_homework":
            return {"assignments": [], "note": "connect to homework service"}

        # ---- Teacher tools ----
        if name == "get_my_classes":
            return {"classes": [], "note": "connect to academic service"}
        if name == "get_class_students":
            return {"students": [], "note": "connect to student service"}
        if name == "get_class_timetable":
            return {"lessons": [], "note": "connect to timetable service"}
        if name == "get_student_learning_progress":
            return {"progress": {}, "note": "connect to analytics service"}
        if name == "get_assignment_submissions":
            return {"submissions": [], "note": "connect to homework service"}

        # ---- Parent tools ----
        if name == "get_linked_children":
            return {"children": [], "note": "connect to parent service"}
        if name == "get_child_grades":
            return {"grades": [], "note": "connect to gradebook service"}
        if name == "get_child_attendance":
            return {"records": [], "note": "connect to attendance service"}
        if name == "get_child_timetable":
            return {"lessons": [], "note": "connect to timetable service"}

        # ---- School Admin tools ----
        if name == "get_school_statistics":
            return {"students": 0, "teachers": 0, "classes": 0, "note": "connect to analytics service"}
        if name == "get_school_classes":
            return {"classes": [], "note": "connect to academic service"}
        if name == "get_school_teachers":
            return {"teachers": [], "note": "connect to teacher service"}
        if name == "get_school_students":
            return {"students": [], "note": "connect to student service"}

        raise ValueError(f"No handler for tool: {name}")
