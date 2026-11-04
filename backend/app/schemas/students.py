"""Student schemas."""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class StudentBase(BaseModel):
    student_number: str = Field(min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = None
    status: str = Field(default="active", max_length=30)


class StudentCreate(StudentBase):
    user_id: UUID
    organization_id: UUID


class StudentUpdate(BaseModel):
    student_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None


class StudentOut(BaseSchema):
    id: UUID
    user_id: UUID
    organization_id: UUID
    student_number: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    status: str
