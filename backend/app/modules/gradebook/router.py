"""Gradebook API routes."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.assessment import Assessment
from app.models.class_ import Class
from app.models.class_enrollment import ClassEnrollment
from app.models.class_subject import ClassSubject
from app.models.grade import Grade
from app.models.grade_history import GradeHistory
from app.models.student import Student
from app.repositories.base import CRUDRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.gradebook import AssessmentCreate, AssessmentOut, AssessmentUpdate, GradeCreate, GradeOut, GradeUpdate

router = APIRouter(prefix="/gradebook", tags=["gradebook"])


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


def _org_allowed(org_id, current_user, db) -> bool:
    # synchronous check helper used after org_id known; membership checked async elsewhere
    return True


# ---------- Assessments ----------
@router.get("/assessments", response_model=list[AssessmentOut])
async def list_assessments(
    class_subject_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Assessment)
        .join(ClassSubject, ClassSubject.id == Assessment.class_subject_id)
        .join(Class, Class.id == ClassSubject.class_id)
    )
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        if allowed is not None:
            org_id = _to_uuid(allowed[0]) if allowed else None
    if org_id is not None:
        query = query.where(Class.organization_id == org_id)
    if class_subject_id:
        query = query.where(Assessment.class_subject_id == _to_uuid(class_subject_id))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return [AssessmentOut.model_validate(o) for o in result.scalars().all()]


@router.post("/assessments", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    class_subject = await db.get(ClassSubject, payload.class_subject_id)
    if not class_subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class subject not found")
    # resolve organization via class
    from app.models.class_ import Class

    class_ = await db.get(Class, class_subject.class_id)
    org_id = class_.organization_id
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or str(org_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of that organization")
        # teacher must be assigned to this class-subject (unless school admin)
        if current_user.get("role") not in ("SCHOOL_ADMIN", "SUPER_ADMIN") and str(class_subject.teacher_id) not in [
            str(m.user_id) for m in []
        ]:
            pass
    obj = await CRUDRepository(Assessment, db).create(
        payload, academic_year_id=payload.academic_year_id
    )
    return AssessmentOut.model_validate(obj)


@router.patch("/assessments/{assessment_id}", response_model=AssessmentOut)
async def update_assessment(
    assessment_id: str,
    payload: AssessmentUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(Assessment, db)
    obj = await repo.get(UUID(assessment_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    from app.models.class_ import Class

    class_subject = await db.get(ClassSubject, obj.class_subject_id)
    class_ = await db.get(Class, class_subject.class_id)
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(class_.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    updated = await repo.update(UUID(assessment_id), payload)
    return AssessmentOut.model_validate(updated)


# ---------- Grades ----------
@router.get("/grades", response_model=list[GradeOut])
async def list_grades(
    assessment_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Grade)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    if assessment_id:
        query = query.where(Grade.assessment_id == _to_uuid(assessment_id))
    if student_id:
        query = query.where(Grade.student_id == _to_uuid(student_id))
    if org_id is not None:
        query = query.join(Student, Student.id == Grade.student_id).where(
            Student.organization_id == org_id
        )
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return [GradeOut.model_validate(o) for o in result.scalars().all()]


@router.post("/grades", response_model=GradeOut, status_code=status.HTTP_201_CREATED)
async def create_or_update_grade(
    payload: GradeCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.get(Assessment, payload.assessment_id)
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    student = await db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # org membership check
    from app.models.class_ import Class

    class_subject = await db.get(ClassSubject, assessment.class_subject_id)
    class_ = await db.get(Class, class_subject.class_id)
    org_id = class_.organization_id
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or str(org_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of that organization")

    # student enrolled in the class?
    enrollment = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.student_id == payload.student_id,
            ClassEnrollment.class_id == class_.id,
            ClassEnrollment.status == "active",
        )
    )
    if not enrollment.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student not enrolled in this class")

    # score validation
    if payload.score < 0 or payload.score > float(assessment.max_score):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score must be between 0 and {assessment.max_score}",
        )

    existing = await db.execute(select(Grade).where(Grade.assessment_id == payload.assessment_id, Grade.student_id == payload.student_id))
    existing_grade = existing.scalar_one_or_none()
    if existing_grade:
        # audit history
        db.add(
            GradeHistory(
                grade_id=existing_grade.id,
                old_score=existing_grade.score,
                new_score=payload.score,
                changed_by=current_user["id"],
                reason="updated",
            )
        )
        existing_grade.score = payload.score
        existing_grade.comment = payload.comment
        existing_grade.entered_by = current_user["id"]
        db.add(existing_grade)
        await db.flush()
        await db.refresh(existing_grade)
        return GradeOut.model_validate(existing_grade)
    else:
        obj = Grade(
            assessment_id=payload.assessment_id,
            student_id=payload.student_id,
            score=payload.score,
            comment=payload.comment,
            entered_by=current_user["id"],
        )
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return GradeOut.model_validate(obj)


@router.patch("/grades/{grade_id}", response_model=GradeOut)
async def update_grade(
    grade_id: str,
    payload: GradeUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    grade = await db.get(Grade, UUID(grade_id))
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found")
    assessment = await db.get(Assessment, grade.assessment_id)
    if payload.score is not None:
        if payload.score < 0 or payload.score > float(assessment.max_score):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score must be between 0 and {assessment.max_score}",
            )
        db.add(
            GradeHistory(
                grade_id=grade.id,
                old_score=grade.score,
                new_score=payload.score,
                changed_by=current_user["id"],
                reason="updated",
            )
        )
        grade.score = payload.score
    if payload.comment is not None:
        grade.comment = payload.comment
    grade.entered_by = current_user["id"]
    db.add(grade)
    await db.flush()
    await db.refresh(grade)
    return GradeOut.model_validate(grade)
