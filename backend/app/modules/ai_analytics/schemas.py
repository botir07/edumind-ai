"""Learning Analytics schemas (Pydantic v2)."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentAnalyticsOut(BaseModel):
    student_id: UUID
    organization_id: UUID
    average_score: Optional[float] = None
    grade_count: int = 0
    attendance_by_status: Dict[str, int] = {}
    submission_count: int = 0
    mastery_by_topic: Dict[str, float] = {}
    topics_needing_practice: List[str] = []
    recent_errors: List[Dict[str, Any]] = []
    active_paths: int = 0
    recommended_exercises: List[Dict[str, Any]] = []


class TeacherClassAnalyticsOut(BaseModel):
    class_id: Optional[UUID] = None
    class_name: Optional[str] = None
    student_count: int = 0
    average_score: Optional[float] = None
    attendance_rate: Optional[float] = None
    mastery_distribution: Dict[str, int] = {}
    common_errors: List[Dict[str, Any]] = []
    students_needing_help: List[Dict[str, Any]] = []


class TeacherAnalyticsOut(BaseModel):
    teacher_id: UUID
    organization_id: UUID
    classes: List[TeacherClassAnalyticsOut] = []
    total_students: int = 0
    overall_average_score: Optional[float] = None


class ParentChildAnalyticsOut(BaseModel):
    student_id: UUID
    student_name: Optional[str] = None
    student_number: Optional[str] = None
    average_score: Optional[float] = None
    attendance_rate: Optional[float] = None
    mastery_by_topic: Dict[str, float] = {}
    recent_errors: List[Dict[str, Any]] = []
    recommended_exercises: List[Dict[str, Any]] = []


class ParentAnalyticsOut(BaseModel):
    parent_id: UUID
    organization_id: UUID
    children: List[ParentChildAnalyticsOut] = []


class SchoolAnalyticsOut(BaseModel):
    organization_id: UUID
    student_count: int = 0
    teacher_count: int = 0
    class_count: int = 0
    average_score: Optional[float] = None
