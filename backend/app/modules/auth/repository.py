"""Authentication repository: data access for auth-related models."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_session import UserSession


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_session(
        self,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at,
        user_agent: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip=ip,
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_session_by_token_hash(self, refresh_token_hash: str) -> Optional[UserSession]:
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == refresh_token_hash,
                UserSession.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, session: UserSession) -> None:
        session.revoked_at = datetime.now(timezone.utc)
        self.session.add(session)

    async def revoke_all_user_sessions(self, user_id: UUID) -> None:
        await self.session.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
