"""FastAPI dependencies: current user, authorization."""
from typing import Optional
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.database.session import get_db
from app.modules.auth.repository import AuthRepository
from app.models.organization_membership import OrganizationMembership


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    access_token: Optional[str] = Cookie(default=None, alias="access_token"),
):
    """Resolve the current authenticated user from the HttpOnly access_token cookie."""
    token = access_token
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(token, settings.secret_key)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    repo = AuthRepository(db)
    user = await repo.get_user_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_superuser": user.is_superuser,
        "locale": user.locale,
    }


def require_role(*allowed_roles: str):
    """Require the current user to hold one of the allowed roles in an active membership."""

    async def checker(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        repo = AuthRepository(db)
        result = await db.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.user_id == current_user["id"],
                OrganizationMembership.is_active == True,  # noqa: E712
            )
        )
        roles = [m.role for m in result.scalars().all()]
        if current_user.get("is_superuser"):
            roles = roles + ["SUPER_ADMIN"]
        if not any(r in allowed_roles for r in roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return checker


async def get_active_memberships(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == current_user["id"],
            OrganizationMembership.is_active == True,  # noqa: E712
        )
    )
    return result.scalars().all()
