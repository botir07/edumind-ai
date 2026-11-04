"""Homework API routes (assignments + submissions)."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.assignment import Assignment
from app.models.assignment_submission import AssignmentSubmission
from app.models.class_enrollment import ClassEnrollment
from app.models.class_ import Class
from app.models.student import Student
from app.models.submission_file import SubmissionFile
from app.models.teacher import Teacher
from app.repositories.base import CRUDRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.homework import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentUpdate,
    SubmissionCreate,
    SubmissionGrade,
    SubmissionOut,
)

router = APIRouter(prefix="/homework", tags=["homework"])

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".txt"}


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


@router.get("/assignments", response_model=list[AssignmentOut])
async def list_assignments(
    class_id: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Assignment)
    if class_id:
        query = query.where(Assignment.class_id == _to_uuid(class_id))
    if teacher_id:
        query = query.where(Assignment.teacher_id == _to_uuid(teacher_id))
    query = query.where(Assignment.is_archived == False)  # noqa: E712
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return [AssignmentOut.model_validate(o) for o in result.scalars().all()]


@router.post("/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AssignmentCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    klass = await db.get(Class, payload.class_id)
    if not klass:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    org_id = klass.organization_id
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or str(org_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of that organization")
    obj = Assignment(
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        teacher_id=current_user["id"],  # teacher creating it; for school admin, falls back below
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        max_score=payload.max_score,
        academic_year_id=payload.academic_year_id,
    )
    # If the current user is a teacher, they must be the teacher of record; allow school admin to set any teacher later.
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return AssignmentOut.model_validate(obj)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(Assignment, UUID(assignment_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    klass = await db.get(Class, obj.class_id)
    org_id = klass.organization_id
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(org_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
        if str(obj.teacher_id) != str(current_user["id"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your assignment")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return AssignmentOut.model_validate(obj)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: str,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(Assignment, UUID(assignment_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    await db.delete(obj)
    await db.flush()
    return None


# ---------- Submissions ----------
@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionOut])
async def list_submissions(
    assignment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == UUID(assignment_id))
    result = await db.execute(query)
    return [SubmissionOut.model_validate(o) for o in result.scalars().all()]


@router.post("/assignments/{assignment_id}/submissions", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    assignment_id: str,
    text_answer: Optional[str] = None,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER", "STUDENT")),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.get(Assignment, UUID(assignment_id))
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    # student must be enrolled in the class
    enrollment = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_id == assignment.class_id,
            ClassEnrollment.status == "active",
        )
    )
    # determine student id from current user's student profile
    student = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student_obj = student.scalar_one_or_none()
    if not student_obj:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can submit")
    if not enrollment.scalar_one_or_none():
        # allow if student is enrolled in that class specifically
        enrollment = await db.execute(
            select(ClassEnrollment).where(
                ClassEnrollment.class_id == assignment.class_id,
                ClassEnrollment.student_id == student_obj.id,
                ClassEnrollment.status == "active",
            )
        )
        if not enrollment.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this class")
    obj = AssignmentSubmission(
        assignment_id=UUID(assignment_id),
        student_id=student_obj.id,
        text_answer=text_answer,
        status="submitted",
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return SubmissionOut.model_validate(obj)


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(AssignmentSubmission, UUID(submission_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return SubmissionOut.model_validate(obj)


@router.patch("/submissions/{submission_id}", response_model=SubmissionOut)
async def grade_submission(
    submission_id: str,
    payload: SubmissionGrade,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(AssignmentSubmission, UUID(submission_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    if payload.grade is not None or payload.feedback is not None:
        obj.graded_at = datetime.now(timezone.utc)
        obj.graded_by = current_user["id"]
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return SubmissionOut.model_validate(obj)


def _validate_upload(file: UploadFile) -> None:
    if file.size and file.size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    import os

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")


@router.post("/submissions/{submission_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_submission_file(
    submission_id: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_upload(file)
    obj = await db.get(AssignmentSubmission, UUID(submission_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    import os, uuid as uuid_module

    safe_name = f"{uuid_module.uuid4().hex}_{os.path.basename(file.filename or 'file')}"
    storage_path = f"uploads/submissions/{safe_name}"
    sf = SubmissionFile(
        submission_id=UUID(submission_id),
        filename=safe_name,
        original_filename=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type,
        size=file.size,
    )
    db.add(sf)
    await db.flush()
    return {"id": str(sf.id), "storage_path": storage_path}
