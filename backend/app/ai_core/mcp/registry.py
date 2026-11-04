"""MCP tool registry with permission metadata.

Tools are registered with strict input schemas and role requirements.
All tools are read-only by default.
"""
from typing import Any, Dict, List, Optional
from app.ai_core.mcp.schemas import ToolDefinition, ToolResult
from app.ai_core.access_control.roles import (
    TOOL_STUDENT, TOOL_TEACHER, TOOL_PARENT, TOOL_SCHOOL_ADMIN, TOOL_PLATFORM,
    ALL_ROLES,
)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self, role: Optional[str] = None) -> List[ToolDefinition]:
        result = []
        for t in self._tools.values():
            if role and t.required_role and t.required_role != role:
                continue
            result.append(t)
        return result

    def category_for_tool(self, name: str) -> Optional[str]:
        t = self._tools.get(name)
        return t.tool_type if t else None


registry = ToolRegistry()


def student_tool(name: str, description: str, input_schema: Dict[str, Any], required_role: str = "STUDENT"):
    return ToolDefinition(
        name=name, description=description, input_schema=input_schema,
        tool_type=TOOL_STUDENT, is_read_only=True, required_role=required_role,
    )


def teacher_tool(name: str, description: str, input_schema: Dict[str, Any], required_role: str = "TEACHER"):
    return ToolDefinition(
        name=name, description=description, input_schema=input_schema,
        tool_type=TOOL_TEACHER, is_read_only=True, required_role=required_role,
    )


def parent_tool(name: str, description: str, input_schema: Dict[str, Any], required_role: str = "PARENT"):
    return ToolDefinition(
        name=name, description=description, input_schema=input_schema,
        tool_type=TOOL_PARENT, is_read_only=True, required_role=required_role,
    )


def school_admin_tool(name: str, description: str, input_schema: Dict[str, Any], required_role: str = "SCHOOL_ADMIN"):
    return ToolDefinition(
        name=name, description=description, input_schema=input_schema,
        tool_type=TOOL_SCHOOL_ADMIN, is_read_only=True, required_role=required_role,
    )
