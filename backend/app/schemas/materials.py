"""Learning materials schemas."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class MaterialBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=50)  # pdf/image/document/video_link/text
    language: str = Field(default="uz", max_length=10)
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    external_url: Optional[str] = None
    is_published: bool = False


class MaterialCreate(MaterialBase):
    organization_id: UUID


class MaterialUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    type: Optional[str] = None
    language: Optional[str] = None
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    external_url: Optional[str] = None
    is_published: Optional[bool] = None


class MaterialOut(BaseSchema):
    id: UUID
    organization_id: UUID
    subject_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    title: str
    type: str
    language: str
    author_id: Optional[UUID] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    external_url: Optional[str] = None
    is_published: bool
