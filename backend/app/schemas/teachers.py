"""Teacher schemas."""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class TeacherBase(BaseModel):
    employee_number: str = Field(min_length=1, max_length=50)
    subject_specialization: Optional[str] = Field(default=None, max_length=150)
    hire_date: Optional[date] = None
    status: str = Field(default="active", max_length=30)


class TeacherCreate(TeacherBase):
    user_id: UUID
    organization_id: UUID


class TeacherUpdate(BaseModel):
    employee_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    subject_specialization: Optional[str] = None
    hire_date: Optional[date] = None
    status: Optional[str] = None


class TeacherOut(BaseSchema):
    id: UUID
    user_id: UUID
    organization_id: UUID
    employee_number: str
    subject_specialization: Optional[str] = None
    hire_date: Optional[date] = None
    status: str
