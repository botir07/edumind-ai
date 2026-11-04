"""Gradebook schemas."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class AssessmentBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    max_score: float = Field(default=100, ge=0)
    weight: float = Field(default=1, ge=0)
    date_assigned: Optional[date] = None
    due_date: Optional[date] = None


class AssessmentCreate(AssessmentBase):
    class_subject_id: UUID
    academic_year_id: UUID


class AssessmentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category: Optional[str] = None
    max_score: Optional[float] = Field(default=None, ge=0)
    weight: Optional[float] = Field(default=None, ge=0)
    date_assigned: Optional[date] = None
    due_date: Optional[date] = None


class AssessmentOut(BaseSchema):
    id: UUID
    class_subject_id: UUID
    title: str
    category: str
    max_score: float
    weight: float
    date_assigned: Optional[date] = None
    due_date: Optional[date] = None
    academic_year_id: UUID


class GradeBase(BaseModel):
    score: float
    comment: Optional[str] = None


class GradeCreate(GradeBase):
    assessment_id: UUID
    student_id: UUID


class GradeUpdate(BaseModel):
    score: Optional[float] = Field(default=None, ge=0)
    comment: Optional[str] = None


class GradeOut(BaseSchema):
    id: UUID
    assessment_id: UUID
    student_id: UUID
    score: float
    comment: Optional[str] = None
    entered_by: Optional[UUID] = None
    entered_at: Optional[datetime] = None
