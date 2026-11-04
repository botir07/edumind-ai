"""MCP (Model Context Protocol) package."""
from app.ai_core.mcp.server import MCPServer  # noqa: F401
from app.ai_core.mcp.registry import ToolRegistry  # noqa: F401
import app.ai_core.mcp.tools  # noqa: F401  (registers all built-in tools)

__all__ = ["MCPServer", "ToolRegistry"]
