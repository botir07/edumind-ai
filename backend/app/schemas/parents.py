"""Parent and guardian schemas."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class ParentBase(BaseModel):
    pass


class ParentCreate(ParentBase):
    user_id: UUID
    organization_id: UUID


class ParentUpdate(BaseModel):
    pass


class ParentOut(BaseSchema):
    id: UUID
    user_id: UUID
    organization_id: UUID


class GuardianCreate(BaseModel):
    student_id: UUID
    parent_id: UUID
    relationship: Optional[str] = Field(default=None, max_length=50)


class GuardianVerify(BaseModel):
    guardian_id: UUID
    is_verified: bool = True


class GuardianOut(BaseSchema):
    id: UUID
    student_id: UUID
    parent_id: UUID
    relationship: Optional[str] = None
    is_verified: bool
