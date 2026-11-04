"""Authentication API routes."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.schemas.auth import (
    LoginRequest,
    MeOut,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/api/v1/auth/refresh",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    payload: LoginRequest,
    service: AuthService = Depends(get_service),
    request: Request = None,
):
    result = await service.login(
        payload.email,
        payload.password,
        user_agent=request.headers.get("user-agent") if request else None,
        ip=request.client.host if request and request.client else None,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    current_user: dict = Depends(get_current_user),
    service: AuthService = Depends(get_service),
):
    await service.logout(current_user["id"])
    _clear_auth_cookies(response)
    return None


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    payload: Optional[RefreshRequest] = None,
    service: AuthService = Depends(get_service),
    request: Request = None,
):
    refresh_token = payload.refresh_token if payload else None
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token") if request else None
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required"
        )
    result = await service.refresh(refresh_token)
    if not result:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
async def password_forgot(
    payload: PasswordResetRequest,
    service: AuthService = Depends(get_service),
):
    token = await service.password_reset_request(payload.email)
    # Always return 202 to avoid user enumeration. In dev, the token is echoed
    # via the X-Dev-Reset-Token header so the flow can be tested without mail.
    response = Response(status_code=status.HTTP_202_ACCEPTED)
    if settings.app_env == "development" and token:
        response.headers["X-Dev-Reset-Token"] = token
    return response


@router.post("/password/reset", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset(
    payload: PasswordResetConfirm,
    service: AuthService = Depends(get_service),
):
    ok = await service.password_reset_confirm(payload.token, payload.new_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
        )
    return None


@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
async def password_change(
    payload: PasswordChange,
    current_user: dict = Depends(get_current_user),
    service: AuthService = Depends(get_service),
):
    ok = await service.password_change(
        current_user["id"], payload.current_password, payload.new_password
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    return None


@router.get("/me", response_model=MeOut)
async def me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.organization_membership import OrganizationMembership
    from app.models.organization import Organization

    result = await db.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            OrganizationMembership.user_id == current_user["id"],
            OrganizationMembership.is_active == True,  # noqa: E712
            Organization.is_active == True,  # noqa: E712
        )
    )
    memberships = []
    for membership, org in result.all():
        memberships.append(
            {
                "id": str(membership.id),
                "organization_id": str(org.id),
                "organization_name": org.name,
                "organization_code": org.code,
                "role": membership.role,
                "is_active": membership.is_active,
            }
        )
    return MeOut(
        user=UserOut(
            id=str(current_user["id"]),
            email=current_user["email"],
            username=current_user["username"],
            full_name=current_user["full_name"],
            phone=None,
            is_active=True,
            is_superuser=current_user["is_superuser"],
            email_verified=True,
            locale=current_user["locale"],
            avatar_url=None,
        ),
        memberships=memberships,
    )
