"""Adaptive Learning schemas (Pydantic v2)."""
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecommendationBase(BaseModel):
    recommendation_type: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    reason: Optional[str] = None
    priority: int = Field(default=1, ge=1)


class RecommendationCreate(RecommendationBase):
    pass


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    organization_id: UUID
    recommendation_type: str
    title: str
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    reason: Optional[str] = None
    priority: int
    is_accepted: bool
    is_dismissed: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RecommendationAction(BaseModel):
    pass


class RecommendationsOut(BaseModel):
    recommendations: List[RecommendationOut] = []
    algorithm_docs: dict = {}
