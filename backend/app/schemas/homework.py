"""Homework schemas."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class AssignmentBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_score: Optional[float] = Field(default=None, ge=0)


class AssignmentCreate(AssignmentBase):
    class_id: UUID
    subject_id: Optional[UUID] = None
    academic_year_id: UUID


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_score: Optional[float] = Field(default=None, ge=0)
    is_archived: Optional[bool] = None


class AssignmentOut(BaseSchema):
    id: UUID
    class_id: UUID
    subject_id: Optional[UUID] = None
    teacher_id: UUID
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_score: Optional[float] = None
    academic_year_id: UUID
    is_archived: bool


class SubmissionBase(BaseModel):
    text_answer: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionOut(BaseSchema):
    id: UUID
    assignment_id: UUID
    student_id: UUID
    text_answer: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    feedback: Optional[str] = None
    grade: Optional[float] = None
    graded_by: Optional[UUID] = None


class SubmissionGrade(BaseModel):
    grade: Optional[float] = Field(default=None, ge=0)
    feedback: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=30)
