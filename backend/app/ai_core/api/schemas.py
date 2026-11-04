"""AI Core API schemas (Pydantic v2). Internal SQLAlchemy models are never returned directly."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PromptTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: str
    language: str = Field(default="uz", max_length=10)
    content: str
    is_active: bool = True


class PromptTemplateCreate(PromptTemplateBase):
    organization_id: Optional[UUID] = None


class PromptTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: Optional[UUID]
    name: str
    role: str
    language: str
    content: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DocumentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    subject: Optional[str] = Field(default=None, max_length=150)
    language: str = Field(default="uz", max_length=10)
    source: Optional[str] = Field(default=None, max_length=100)
    access_level: str = Field(default="org", max_length=30)
    file_path: Optional[str] = None
    mime_type: Optional[str] = Field(default=None, max_length=100)
    size_bytes: Optional[int] = None
    checksum: str
    processing_status: str = Field(default="pending", max_length=30)


class DocumentCreate(DocumentBase):
    organization_id: UUID


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    title: str
    subject: Optional[str]
    language: str
    source: Optional[str]
    access_level: str
    version: int
    checksum: str
    file_path: Optional[str]
    mime_type: Optional[str]
    size_bytes: Optional[int]
    processing_status: str
    created_at: datetime
    updated_at: datetime


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=10, ge=1, le=50)
    subject: Optional[str] = None
    language: Optional[str] = None


class RagSearchResult(BaseModel):
    document_id: UUID
    content: str
    score: float
    source_title: Optional[str]
    subject: Optional[str]
    page: Optional[int]
    section: Optional[int]


class RagSearchResponse(BaseModel):
    chunks: List[RagSearchResult]
    citations: List[Dict[str, Any]]
    total_returned: int
    query_hash: str


class ToolExecuteRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolExecuteResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class TraceOut(BaseModel):
    trace_id: str
    organization_id: Optional[UUID]
    user_id: Optional[UUID]
    operation: Optional[str]
    status: Optional[str]
    latency_ms: Optional[int]
    created_at: datetime


class SecurityEventOut(BaseModel):
    id: UUID
    event_type: str
    severity: str
    organization_id: Optional[UUID]
    user_id: Optional[UUID]
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    service: str = "ai_core"
    components: Dict[str, Any]


class ConfigStatusResponse(BaseModel):
    ai_core_enabled: bool
    rag_enabled: bool
    mcp_enabled: bool
    cache_enabled: bool
    trace_enabled: bool
    providers: List[str]
    default_llm_provider: Optional[str]
    default_embedding_provider: Optional[str]
