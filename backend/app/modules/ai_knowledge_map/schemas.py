"""Knowledge Map schemas (Pydantic v2)."""
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- Knowledge hierarchy ----------

class KnowledgeSubjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: Optional[str] = Field(default=None, max_length=20)


class KnowledgeSubjectCreate(KnowledgeSubjectBase):
    organization_id: UUID


class KnowledgeSubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    code: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class KnowledgeTopicBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: Optional[str] = Field(default=None, max_length=20)
    order_index: int = Field(default=0, ge=0)


class KnowledgeTopicCreate(KnowledgeTopicBase):
    subject_id: UUID


class KnowledgeTopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_id: UUID
    name: str
    code: Optional[str] = None
    order_index: int
    created_at: datetime
    updated_at: datetime


class KnowledgeSubtopicBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: Optional[str] = Field(default=None, max_length=20)
    order_index: int = Field(default=0, ge=0)


class KnowledgeSubtopicCreate(KnowledgeSubtopicBase):
    topic_id: UUID


class KnowledgeSubtopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_id: UUID
    name: str
    code: Optional[str] = None
    order_index: int
    created_at: datetime
    updated_at: datetime


class KnowledgeSkillBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: Optional[str] = Field(default=None, max_length=20)
    order_index: int = Field(default=0, ge=0)


class KnowledgeSkillCreate(KnowledgeSkillBase):
    subtopic_id: UUID


class KnowledgeSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subtopic_id: UUID
    name: str
    code: Optional[str] = None
    order_index: int
    created_at: datetime
    updated_at: datetime


# ---------- Student knowledge state ----------

class KnowledgeStateBase(BaseModel):
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    subtopic_id: Optional[UUID] = None
    skill_id: Optional[UUID] = None


class KnowledgeStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    organization_id: UUID
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    subtopic_id: Optional[UUID] = None
    skill_id: Optional[UUID] = None
    mastery_score: float
    confidence: float
    attempt_count: int
    correct_answers: int
    incorrect_answers: int
    last_practiced_at: Optional[datetime] = None
    last_assessed_at: Optional[datetime] = None
    learning_status: str
    evidence_references: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


class KnowledgeMapOut(BaseModel):
    """Full knowledge map for a student: hierarchy + mastery states."""
    subjects: List[KnowledgeSubjectOut] = []
    topics: List[KnowledgeTopicOut] = []
    subtopics: List[KnowledgeSubtopicOut] = []
    skills: List[KnowledgeSkillOut] = []
    mastery_states: List[KnowledgeStateOut] = []
