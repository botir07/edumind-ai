"""Academic structure schemas."""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema


class AcademicYearBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearCreate(AcademicYearBase):
    pass


class AcademicYearUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None


class AcademicYearOut(BaseSchema):
    id: UUID
    organization_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool


class GradeLevelBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    level_order: int


class GradeLevelCreate(GradeLevelBase):
    pass


class GradeLevelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    level_order: Optional[int] = None


class GradeLevelOut(BaseSchema):
    id: UUID
    organization_id: UUID
    name: str
    level_order: int


class ClassBase(BaseModel):
    grade_id: Optional[UUID] = None
    name: str = Field(min_length=1, max_length=50)
    room_teacher_id: Optional[UUID] = None
    capacity: Optional[int] = None


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    grade_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    room_teacher_id: Optional[UUID] = None
    capacity: Optional[int] = None


class ClassOut(BaseSchema):
    id: UUID
    organization_id: UUID
    grade_id: Optional[UUID] = None
    name: str
    room_teacher_id: Optional[UUID] = None
    capacity: Optional[int] = None


class SubjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: Optional[str] = Field(default=None, max_length=20)


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    code: Optional[str] = None


class SubjectOut(BaseSchema):
    id: UUID
    organization_id: UUID
    name: str
    code: Optional[str] = None


class TopicBase(BaseModel):
    subject_id: UUID
    name: str = Field(min_length=1, max_length=150)
    order_index: int = 0


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    order_index: Optional[int] = None


class TopicOut(BaseSchema):
    id: UUID
    subject_id: UUID
    name: str
    order_index: int


class CurriculumVersionBase(BaseModel):
    academic_year_id: Optional[UUID] = None
    name: str = Field(min_length=1, max_length=150)
    is_active: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CurriculumVersionCreate(CurriculumVersionBase):
    pass


class CurriculumVersionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    is_active: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CurriculumVersionOut(BaseSchema):
    id: UUID
    organization_id: UUID
    academic_year_id: Optional[UUID] = None
    name: str
    is_active: bool
    start_date: Optional[date] = None
    end_date: Optional[date] = None
