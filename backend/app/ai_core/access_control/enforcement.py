"""Access Control enforcement for AI Core.

Provides permission checks used before RAG retrieval, before MCP tool execution,
and before AI administrative operations. Reuses Phase 1 auth dependencies
(get_current_user / require_role) at the route layer; this class contains the
business logic.
"""
from typing import List, Optional
from uuid import UUID

from app.ai_core.access_control.roles import (
    ACTION_ADMIN,
    ACTION_INGEST,
    ACTION_READ,
    ACTION_RETRIEVE,
    ACTION_WRITE,
    RESOURCE_DOCUMENT,
    RESOURCE_TOOL,
    ROLE_MAX_TOP_K,
    ROLE_TOOL_CATEGORIES,
    ALL_ROLES,
)
from app.ai_core.access_control.tenant_scope import is_member_of, user_org_ids


class AICoreEnforcer:
    def __init__(self, session, user_id: UUID):
        self.session = session
        self.user_id = user_id
        self._org_ids: Optional[List[UUID]] = None

    async def org_ids(self) -> List[UUID]:
        if self._org_ids is None:
            self._org_ids = await user_org_ids(self.session, self.user_id)
        return self._org_ids

    async def can_access_org(self, org_id: UUID) -> bool:
        ids = await self.org_ids()
        return org_id in ids

    async def require_org_access(self, org_id: UUID) -> None:
        if not await self.can_access_org(org_id):
            from app.ai_core.core.exceptions import AIAuthorizationError
            raise AIAuthorizationError(
                "Not a member of the requested organization",
                details={"organization_id": str(org_id)},
            )

    # ---------- tool permissions ----------

    async def user_roles(self) -> List[str]:
        from sqlalchemy import select
        from app.models.organization_membership import OrganizationMembership

        result = await self.session.execute(
            select(OrganizationMembership.role).where(
                OrganizationMembership.user_id == self.user_id,
                OrganizationMembership.is_active == True,  # noqa: E712
            )
        )
        # row may be 1-tuple (role,) from real SQLAlchemy or 2-tuple (org_id, role)
        # from the test stub; handle both.
        roles = [row[1] if len(row) > 1 else row[0] for row in result.all()]
        return roles

    async def may_execute_tool(self, tool_category: str, required_role: Optional[str] = None) -> bool:
        roles = await self.user_roles()
        allowed = False
        for role in roles:
            if tool_category in ROLE_TOOL_CATEGORIES.get(role, []):
                allowed = True
            if role == "SUPER_ADMIN":
                allowed = True
        if required_role and required_role not in roles:
            allowed = False
        return allowed

    async def require_tool_access(self, tool_category: str, required_role: Optional[str] = None) -> None:
        if not await self.may_execute_tool(tool_category, required_role):
            from app.ai_core.core.exceptions import AIAuthorizationError
            raise AIAuthorizationError(
                f"Not permitted to execute {tool_category} tool",
                details={"tool_category": tool_category, "required_role": required_role},
            )

    # ---------- RAG document permissions ----------

    async def max_top_k(self) -> int:
        roles = await self.user_roles()
        # most permissive among user's roles
        return max((ROLE_MAX_TOP_K.get(r, 5) for r in roles), default=5)

    async def may_retrieve_document(self, document_org_id: UUID) -> bool:
        return await self.can_access_org(document_org_id)

    async def require_document_access(self, document_org_id: UUID) -> None:
        if not await self.may_retrieve_document(document_org_id):
            from app.ai_core.core.exceptions import AIAuthorizationError
            raise AIAuthorizationError(
                "Not permitted to access this document",
                details={"organization_id": str(document_org_id)},
            )

    # ---------- resource-level access ----------

    async def may_access_resource(self, resource_type: str, resource_org_id: UUID, action: str) -> bool:
        # Base rule: user must be member of the resource's organization
        if not await self.can_access_org(resource_org_id):
            return False
        # Write/admin actions restricted to staff roles
        if action in (ACTION_WRITE, ACTION_ADMIN, ACTION_INGEST):
            roles = await self.user_roles()
            if not any(r in ("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER") for r in roles):
                return False
        return True

    async def require_resource_access(
        self, resource_type: str, resource_org_id: UUID, action: str
    ) -> None:
        if not await self.may_access_resource(resource_type, resource_org_id, action):
            from app.ai_core.core.exceptions import AIAuthorizationError
            raise AIAuthorizationError(
                f"Not permitted to {action} {resource_type}",
                details={"resource_type": resource_type, "action": action, "organization_id": str(resource_org_id)},
            )
