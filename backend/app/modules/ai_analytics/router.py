"""Learning Analytics API routes (/api/v1/ai/analytics/*).

Real database-driven analytics for student, teacher, and parent. Role-scoped.
"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.models.phase3_tables import AIStudentKnowledgeState
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models import (
    AssignmentSubmission,
    AttendanceRecord,
    Class as ClassModel,
    Grade,
    OrganizationMembership,
    Parent,
    Student,
    Teacher,
    Teacher as TeacherModel,
)

from .schemas import (
    ParentAnalyticsOut,
    SchoolAnalyticsOut,
    StudentAnalyticsOut,
    TeacherAnalyticsOut,
)
from .service import LearningAnalyticsService

router = APIRouter(prefix="/ai/analytics", tags=["ai_analytics"])


def _build_service(db: AsyncSession, enforcer) -> LearningAnalyticsService:
    return LearningAnalyticsService(session=db, enforcer=enforcer)


async def _get_staff_roles(db: AsyncSession, current_user: dict) -> list:
    result = await db.execute(
        select(OrganizationMembership.role).where(
            OrganizationMembership.user_id == current_user["id"],
            OrganizationMembership.is_active == True,  # noqa: E712
        )
    )
    return [row[0] for row in result.all()]


@router.get("/student/{student_id}", response_model=StudentAnalyticsOut)
async def student_analytics(
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    viewer_result = await db.execute(
        select(Student).where(Student.user_id == current_user["id"])
    )
    viewer = viewer_result.scalar_one_or_none()
    if not viewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
    await enforcer.require_org_access(viewer.organization_id)

    target_student = await db.get(Student, student_id)
    if not target_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    await enforcer.require_org_access(target_student.organization_id)

    roles = await _get_staff_roles(db, current_user)
    is_self = viewer.id == target_student.id
    is_staff = any(r in ("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER", "PARENT") for r in roles)
    if not (is_self or is_staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted")

    service = _build_service(db, enforcer)
    return await service.student_analytics(
        student_id=student_id, organization_id=target_student.organization_id
    )


@router.get("/teacher/{teacher_id}", response_model=TeacherAnalyticsOut)
async def teacher_analytics(
    teacher_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    roles = await _get_staff_roles(db, current_user)
    if not any(r in ("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER") for r in roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff only")

    target = await db.get(Teacher, teacher_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    await enforcer.require_org_access(target.organization_id)

    service = _build_service(db, enforcer)
    return await service.teacher_analytics(
        teacher_id=teacher_id, organization_id=target.organization_id
    )


@router.get("/parent/{parent_id}", response_model=ParentAnalyticsOut)
async def parent_analytics(
    parent_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    roles = await _get_staff_roles(db, current_user)
    if not any(r in ("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER", "PARENT") for r in roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted")

    target = await db.get(Parent, parent_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found")
    await enforcer.require_org_access(target.organization_id)

    service = _build_service(db, enforcer)
    return await service.parent_analytics(
        parent_id=parent_id, organization_id=target.organization_id
    )


@router.get("/school/{organization_id}", response_model=SchoolAnalyticsOut)
async def school_analytics(
    organization_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    roles = await _get_staff_roles(db, current_user)
    if not any(r in ("SUPER_ADMIN", "SCHOOL_ADMIN") for r in roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    await enforcer.require_org_access(organization_id)

    student_count_result = await db.execute(
        select(func.count(Student.id)).where(Student.organization_id == organization_id)
    )
    student_count = student_count_result.scalar_one_or_none() or 0

    teacher_count_result = await db.execute(
        select(func.count(TeacherModel.id)).where(TeacherModel.organization_id == organization_id)
    )
    teacher_count = teacher_count_result.scalar_one_or_none() or 0

    class_count_result = await db.execute(
        select(func.count(ClassModel.id)).where(ClassModel.organization_id == organization_id)
    )
    class_count = class_count_result.scalar_one_or_none() or 0

    avg_result = await db.execute(
        select(func.avg(Grade.score)).join(Student, Student.id == Grade.student_id).where(
            Student.organization_id == organization_id
        )
    )
    avg_score = avg_result.scalar_one_or_none()

    return SchoolAnalyticsOut(
        organization_id=organization_id,
        student_count=student_count,
        teacher_count=teacher_count,
        class_count=class_count,
        average_score=round(float(avg_score), 2) if avg_score is not None else None,
    )
