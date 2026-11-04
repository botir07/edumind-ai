"""Tenant scope resolution for AI Core.

Organization scope is resolved server-side from the user's active memberships
(Phase 1 organization_memberships). Never trusted from client parameters.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_membership import OrganizationMembership


async def resolve_organization_scope(
    session: AsyncSession,
    user_id: UUID,
    requested_org_id: Optional[UUID] = None,
) -> List[UUID]:
    """Return the list of organization IDs the user may access.

    If requested_org_id is given, it is included only if the user is an active
    member of that organization. Otherwise returns all active membership orgs.
    Superuser is not auto-granted all orgs here; callers decide superuser scope.
    """
    result = await session.execute(
        select(OrganizationMembership.organization_id).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active == True,  # noqa: E712
        )
    )
    org_ids = [row[0] for row in result.all()]

    if requested_org_id is not None:
        if requested_org_id not in org_ids:
            return []  # not a member -> empty scope
        return [requested_org_id]

    return org_ids


async def user_org_ids(session: AsyncSession, user_id: UUID) -> List[UUID]:
    """Convenience: all active org IDs for a user."""
    return await resolve_organization_scope(session, user_id, None)


async def is_member_of(
    session: AsyncSession, user_id: UUID, org_id: UUID
) -> bool:
    ids = await resolve_organization_scope(session, user_id, org_id)
    return org_id in ids
