"""Access Control: FastAPI dependency helpers.

Wraps AICoreEnforcer for use in route dependencies alongside Phase 1
get_current_user / require_role.
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.core.dependencies import get_current_user
from app.database.session import get_db


async def get_ai_enforcer(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AICoreEnforcer:
    """Build an AICoreEnforcer for the current authenticated user."""
    return AICoreEnforcer(session=db, user_id=current_user["id"])


async def require_ai_org_access(
    org_id: UUID,
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
) -> AICoreEnforcer:
    """Dependency: ensure the user may access the given organization."""
    await enforcer.require_org_access(org_id)
    return enforcer


async def require_ai_tool_access(
    tool_category: str,
    required_role: Optional[str] = None,
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
) -> AICoreEnforcer:
    """Dependency: ensure the user may execute the given tool category."""
    await enforcer.require_tool_access(tool_category, required_role)
    return enforcer


async def require_ai_document_access(
    document_org_id: UUID,
    enforcer: AICoreEnforcer = Depends(get_ai_enforcer),
) -> AICoreEnforcer:
    """Dependency: ensure the user may access the given document's org."""
    await enforcer.require_document_access(document_org_id)
    return enforcer
