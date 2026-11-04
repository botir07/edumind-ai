"""Notifications schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class NotificationBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str
    type: str = Field(default="info", max_length=50)


class NotificationCreate(NotificationBase):
    organization_id: UUID
    recipient_user_id: UUID


class NotificationOut(BaseSchema):
    id: UUID
    organization_id: UUID
    recipient_user_id: UUID
    title: str
    body: str
    type: str
    is_read: bool
    read_at: Optional[datetime] = None



class NotificationPreferenceBase(BaseModel):
    channel: str = Field(min_length=1, max_length=30)
    enabled: bool = True


class NotificationPreferenceCreate(NotificationPreferenceBase):
    user_id: UUID


class NotificationPreferenceOut(BaseSchema):
    id: UUID
    user_id: UUID
    channel: str
    enabled: bool
