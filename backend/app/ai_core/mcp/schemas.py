"""MCP tool schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    name: str
    type: str  # string, integer, boolean, array, object
    description: Optional[str] = None
    required: bool = False


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON Schema
    output_schema: Optional[Dict[str, Any]] = None
    tool_type: str  # student/teacher/parent/school_admin/platform
    is_read_only: bool = True
    is_active: bool = True
    required_role: Optional[str] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    user_id: str
    organization_id: str


class ToolResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
