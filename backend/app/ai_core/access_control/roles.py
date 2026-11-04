"""Access Control roles and permissions constants for AI Core.

Reuses Phase 1 roles (SUPER_ADMIN, SCHOOL_ADMIN, TEACHER, STUDENT, PARENT)
via organization_memberships. No parallel user/role system.
"""

# AI Core-specific actions
ACTION_READ = "read"
ACTION_WRITE = "write"
ACTION_EXECUTE = "execute"
ACTION_INGEST = "ingest"
ACTION_RETRIEVE = "retrieve"
ACTION_ADMIN = "admin"

# Resource types
RESOURCE_PROMPT = "prompt"
RESOURCE_DOCUMENT = "document"
RESOURCE_CHUNK = "chunk"
RESOURCE_TOOL = "tool"
RESOURCE_TRACE = "trace"
RESOURCE_SECURITY_EVENT = "security_event"
RESOURCE_CACHE = "cache"

# Tool categories
TOOL_STUDENT = "student"
TOOL_TEACHER = "teacher"
TOOL_PARENT = "parent"
TOOL_SCHOOL_ADMIN = "school_admin"
TOOL_PLATFORM = "platform"

ALL_ROLES = ["SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER", "STUDENT", "PARENT"]

# Default role -> allowed tool categories (read-only by default)
ROLE_TOOL_CATEGORIES = {
    "SUPER_ADMIN": [TOOL_STUDENT, TOOL_TEACHER, TOOL_PARENT, TOOL_SCHOOL_ADMIN, TOOL_PLATFORM],
    "SCHOOL_ADMIN": [TOOL_STUDENT, TOOL_TEACHER, TOOL_PARENT, TOOL_SCHOOL_ADMIN],
    "TEACHER": [TOOL_TEACHER, TOOL_STUDENT],
    "PARENT": [TOOL_PARENT],
    "STUDENT": [TOOL_STUDENT],
}

# Default role -> max RAG top_k (prevent over-fetching)
ROLE_MAX_TOP_K = {
    "SUPER_ADMIN": 20,
    "SCHOOL_ADMIN": 20,
    "TEACHER": 15,
    "PARENT": 10,
    "STUDENT": 10,
}
