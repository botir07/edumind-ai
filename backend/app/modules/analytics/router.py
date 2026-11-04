"""Analytics API routes (real database aggregations)."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.assignment_submission import AssignmentSubmission
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.class_enrollment import ClassEnrollment
from app.models.grade import Grade
from app.models.student import Student

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _to_uuid(value) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(value)


async def _member_org_ids(current_user, db: AsyncSession):
    if current_user.get("is_superuser"):
        return None
    memberships = await get_active_memberships(current_user, db)
    return [str(m.organization_id) for m in memberships]


@router.get("/student/{student_id}")
async def student_analytics(
    student_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await db.get(Student, UUID(student_id))
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    # parents/teachers: only if authorized (simplified: org membership)
    org_id = student.organization_id
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or str(org_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    avg_result = await db.execute(
        select(func.avg(Grade.score)).where(Grade.student_id == UUID(student_id))
    )
    avg_score = avg_result.scalar_one_or_none()
    grade_count_result = await db.execute(select(func.count(Grade.id)).where(Grade.student_id == UUID(student_id)))
    grade_count = grade_count_result.scalar_one_or_none() or 0
    attendance_result = await db.execute(
        select(AttendanceRecord.status, func.count(AttendanceRecord.id))
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(AttendanceRecord.student_id == UUID(student_id))
        .group_by(AttendanceRecord.status)
    )
    attendance = {row[0]: row[1] for row in attendance_result.all()}
    submission_result = await db.execute(
        select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.student_id == UUID(student_id))
    )
    submissions = submission_result.scalar_one_or_none() or 0
    return {
        "student_id": student_id,
        "average_score": float(avg_score) if avg_score is not None else None,  # None = no grades (missing vs zero)
        "grade_count": grade_count,
        "attendance_by_status": attendance,
        "submission_count": submissions,
    }


@router.get("/school/{org_id}")
async def school_analytics(
    org_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = _to_uuid(org_id)
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or str(org_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    students = await db.execute(select(func.count(Student.id)).where(Student.organization_id == org_id))
    teachers_count = 0
    from app.models.teacher import Teacher

    teachers_result = await db.execute(select(func.count(Teacher.id)).where(Teacher.organization_id == org_id))
    teachers_count = teachers_result.scalar_one_or_none() or 0
    classes_result = await db.execute(
        select(func.count(__import__("app.models.class_", fromlist=["Class"]).Class.id)).where(
            __import__("app.models.class_", fromlist=["Class"]).Class.organization_id == org_id
        )
    )
    class_count = classes_result.scalar_one_or_none() or 0
    avg_result = await db.execute(
        select(func.avg(Grade.score)).join(Student, Student.id == Grade.student_id).where(
            Student.organization_id == org_id
        )
    )
    avg_score = avg_result.scalar_one_or_none()
    return {
        "organization_id": str(org_id),
        "student_count": students.scalar_one_or_none() or 0,
        "teacher_count": teachers_count,
        "class_count": class_count,
        "average_score": float(avg_score) if avg_score is not None else None,
    }
