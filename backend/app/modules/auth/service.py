"""Authentication service: login, logout, refresh, password reset/change."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.repository import AuthRepository


class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    async def authenticate(self, email: str, password: str):
        user = await self.repository.get_user_by_email(email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def issue_tokens(self, user) -> tuple[str, str, datetime]:
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        # store refresh token hash
        from passlib.context import CryptContext

        pwd_context = CryptContext(
            schemes=["argon2"], deprecated="auto", argon2__type="id"
        )
        refresh_hash = pwd_context.hash(refresh_token)
        await self.repository.create_session(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            expires_at=expires_at,
        )
        return access_token, refresh_token, expires_at

    async def login(self, email: str, password: str, user_agent: Optional[str] = None, ip: Optional[str] = None):
        user = await self.authenticate(email, password)
        if not user:
            return None
        access_token, refresh_token, expires_at = await self.issue_tokens(user)
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }

    async def refresh(self, refresh_token: str):
        payload = decode_token(refresh_token, settings.refresh_secret_key)
        if not payload or payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        user = await self.repository.get_user_by_id(UUID(user_id))
        if not user or not user.is_active:
            return None
        # Rotate refresh tokens: revoke all sessions for user and issue new ones.
        await self.repository.revoke_all_user_sessions(user.id)
        access_token, new_refresh_token, expires_at = await self.issue_tokens(user)
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_at": expires_at,
        }

    async def logout(self, user_id: UUID) -> None:
        await self.repository.revoke_all_user_sessions(user_id)

    async def password_reset_request(self, email: str) -> Optional[str]:
        """Issue a short-lived password-reset JWT (self-contained, no storage)."""
        user = await self.repository.get_user_by_email(email)
        if not user:
            return None  # do not reveal whether email exists
        from app.core.security import create_access_token

        # reuse access-token signer with a very short expiry and a reset type
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode = {"sub": str(user.id), "exp": expire, "type": "password_reset"}
        from jose import jwt

        token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return token

    async def password_reset_confirm(self, token: str, new_password: str) -> bool:
        from jose import JWTError, jwt

        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except JWTError:
            return False
        if payload.get("type") != "password_reset":
            return False
        user = await self.repository.get_user_by_id(UUID(payload["sub"]))
        if not user:
            return False
        user.hashed_password = get_password_hash(new_password)
        user.email_verified = True
        self.repository.session.add(user)
        await self.repository.session.flush()
        # revoke all sessions on password reset
        await self.repository.revoke_all_user_sessions(user.id)
        return True

    async def password_change(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        user = await self.repository.get_user_by_id(user_id)
        if not user or not verify_password(current_password, user.hashed_password):
            return False
        user.hashed_password = get_password_hash(new_password)
        self.repository.session.add(user)
        await self.repository.session.flush()
        await self.repository.revoke_all_user_sessions(user.id)
        return True
