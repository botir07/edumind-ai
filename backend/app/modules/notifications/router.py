"""Notifications API routes."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.repositories.base import CRUDRepository
from app.schemas.notifications import (
    NotificationCreate,
    NotificationOut,
    NotificationPreferenceCreate,
    NotificationPreferenceOut,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_uuid(value) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(value)


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    recipient_user_id: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # users see their own notifications unless superuser/school admin querying
    query = select(Notification)
    if recipient_user_id:
        query = query.where(Notification.recipient_user_id == _to_uuid(recipient_user_id))
    else:
        query = query.where(Notification.recipient_user_id == current_user["id"])
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
    result = await db.execute(query)
    return [NotificationOut.model_validate(o) for o in result.scalars().all()]


@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(Notification, db)
    obj = await repo.create(payload)
    return NotificationOut.model_validate(obj)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(Notification, UUID(notification_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if obj.recipient_user_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification")
    obj.is_read = True
    obj.read_at = datetime.now(timezone.utc)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return NotificationOut.model_validate(obj)


@router.get("/preferences", response_model=list[NotificationPreferenceOut])
async def list_preferences(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(NotificationPreference).where(NotificationPreference.user_id == current_user["id"])
    result = await db.execute(query)
    return [NotificationPreferenceOut.model_validate(o) for o in result.scalars().all()]


@router.patch("/preferences/{channel}", response_model=NotificationPreferenceOut)
async def update_preference(
    channel: str,
    enabled: bool = Query(True),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user["id"],
            NotificationPreference.channel == channel,
        )
    )
    obj = obj.scalar_one_or_none()
    if not obj:
        obj = NotificationPreference(user_id=current_user["id"], channel=channel, enabled=enabled)
        db.add(obj)
    else:
        obj.enabled = enabled
        db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return NotificationPreferenceOut.model_validate(obj)

