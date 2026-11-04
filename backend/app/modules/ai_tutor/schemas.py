"""AI Tutor schemas (Pydantic v2). Internal SQLAlchemy models never returned directly."""
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- Tutor session ----------

class TutorSessionBase(BaseModel):
    mode: str = Field(default="explain", max_length=30)
    locale: str = Field(default="uz", max_length=10)
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, max_length=200)


class TutorSessionCreate(TutorSessionBase):
    pass


class TutorSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    organization_id: UUID
    mode: str
    locale: str
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    title: Optional[str] = None
    is_active: bool
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ---------- Tutor message ----------

class TutorMessageBase(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    mode: Optional[str] = Field(default=None, max_length=30)


class TutorMessageCreate(TutorMessageBase):
    pass


class TutorMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str
    mode: Optional[str] = None
    trace_id: Optional[str] = None
    citations: Optional[Any] = None
    provider: Optional[str] = None
    usage: Optional[Any] = None
    latency_ms: Optional[int] = None
    created_at: datetime


# ---------- Tutor chat (send message + get response) ----------

class TutorChatRequest(BaseModel):
    session_id: Optional[UUID] = None  # if omitted, a new session is created
    message: str = Field(min_length=1, max_length=4000)
    mode: Optional[str] = Field(default="explain", max_length=30)
    locale: Optional[str] = Field(default="uz", max_length=10)
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    use_rag: bool = False
    use_mcp: bool = False
    use_cache: bool = False
    top_k: int = Field(default=10, ge=1, le=50)


class TutorChatResponse(BaseModel):
    session_id: UUID
    message_id: UUID
    content: str
    citations: List[Any] = []
    sanitized: bool = False
    provider: str = "none"
    model: Optional[str] = None
    usage: Any = {}
    trace_id: str


# ---------- Session list / detail ----------

class TutorSessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mode: str
    locale: str
    title: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class TutorSessionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    organization_id: UUID
    mode: str
    locale: str
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    title: Optional[str] = None
    is_active: bool
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    messages: List[TutorMessageOut] = []
