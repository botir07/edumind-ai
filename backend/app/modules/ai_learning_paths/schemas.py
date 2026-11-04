"""Learning Paths schemas (Pydantic v2)."""
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LearningPathStepBase(BaseModel):
    step_number: int = Field(ge=1)
    step_type: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    topic_id: Optional[UUID] = None
    is_required: bool = True


class LearningPathStepCreate(LearningPathStepBase):
    pass


class LearningPathStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    path_id: UUID
    step_number: int
    step_type: str
    title: str
    description: Optional[str] = None
    topic_id: Optional[UUID] = None
    is_required: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LearningPathBase(BaseModel):
    subject_id: Optional[UUID] = None
    target_topic_id: Optional[UUID] = None
    title: str = Field(min_length=1, max_length=200)
    difficulty: Optional[str] = Field(default=None, max_length=20)


class LearningPathCreate(LearningPathBase):
    steps: List[LearningPathStepCreate] = []


class LearningPathOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    organization_id: UUID
    subject_id: Optional[UUID] = None
    target_topic_id: Optional[UUID] = None
    title: str
    difficulty: Optional[str] = None
    status: str
    progress: float
    created_at: datetime
    updated_at: datetime
    steps: List[LearningPathStepOut] = []


class LearningPathUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    difficulty: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=30)


class StepComplete(BaseModel):
    score: Optional[float] = Field(default=None, ge=0, le=100)


LearningPathStepComplete = StepComplete
