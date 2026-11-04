"""Timetable schemas."""
from datetime import time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class RoomBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    capacity: Optional[int] = Field(default=None, ge=0)


class RoomCreate(RoomBase):
    organization_id: UUID


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(default=None, ge=0)


class RoomOut(BaseSchema):
    id: UUID
    organization_id: UUID
    name: str
    capacity: Optional[int] = None


class LessonBase(BaseModel):
    subject_id: Optional[UUID] = None
    day_of_week: int = Field(ge=1, le=7)
    start_time: time  # HH:MM
    end_time: time


class LessonCreate(LessonBase):
    class_id: UUID
    teacher_id: UUID
    room_id: Optional[UUID] = None
    academic_year_id: UUID


class LessonUpdate(BaseModel):
    subject_id: Optional[UUID] = None
    day_of_week: Optional[int] = Field(default=None, ge=1, le=7)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    teacher_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    is_cancelled: Optional[bool] = None
    replacement_teacher_id: Optional[UUID] = None


class LessonOut(BaseSchema):
    id: UUID
    class_id: UUID
    subject_id: Optional[UUID] = None
    teacher_id: UUID
    room_id: Optional[UUID] = None
    day_of_week: int
    start_time: time
    end_time: time
    academic_year_id: UUID
    is_cancelled: bool
    replacement_teacher_id: Optional[UUID] = None
