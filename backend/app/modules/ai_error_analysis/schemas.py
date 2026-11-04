"""Error Analysis schemas (Pydantic v2)."""
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ErrorCategoryBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = None


class ErrorCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    created_at: datetime


class ErrorAnalysisBase(BaseModel):
    student_id: Optional[UUID] = None
    attempt_id: Optional[UUID] = None
    error_type: str = Field(min_length=1, max_length=50)
    question: str = Field(min_length=1)
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    topic_id: Optional[UUID] = None
    recommended_exercise: Optional[str] = None


class ErrorAnalysisCreate(ErrorAnalysisBase):
    pass


class ErrorAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    organization_id: UUID
    attempt_id: Optional[UUID] = None
    error_category_id: Optional[UUID] = None
    error_type: str
    question: str
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    topic_id: Optional[UUID] = None
    recommended_exercise: Optional[str] = None
    created_at: datetime


class ErrorAnalysisRequest(BaseModel):
    """Request to analyze a student answer."""
    attempt_id: Optional[UUID] = None
    question: str = Field(min_length=1)
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    topic_id: Optional[UUID] = None
