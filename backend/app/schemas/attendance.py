"""Attendance schemas."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class AttendanceSessionBase(BaseModel):
    subject_id: Optional[UUID] = None
    session_date: date


class AttendanceSessionCreate(AttendanceSessionBase):
    class_id: UUID
    teacher_id: UUID
    academic_year_id: UUID


class AttendanceSessionOut(BaseSchema):
    id: UUID
    class_id: UUID
    subject_id: Optional[UUID] = None
    teacher_id: UUID
    date: date
    academic_year_id: UUID


class AttendanceRecordBase(BaseModel):
    status: str = Field(min_length=1, max_length=20)  # present/absent/late/excused
    note: Optional[str] = None


class AttendanceRecordCreate(AttendanceRecordBase):
    student_id: UUID


class AttendanceRecordOut(BaseSchema):
    id: UUID
    session_id: UUID
    student_id: UUID
    status: str
    marked_by: Optional[UUID] = None
    marked_at: Optional[datetime] = None
    note: Optional[str] = None

