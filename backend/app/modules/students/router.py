"""Student API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.class_enrollment import ClassEnrollment
from app.models.organization import Organization
from app.models.student import Student
from app.models.user import User
from app.repositories.base import CRUDRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.students import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


def _repo(db: AsyncSession) -> CRUDRepository:
    return CRUDRepository(Student, db)


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


@router.get("", response_model=PaginatedResponse[StudentOut])
async def list_students(
    organization_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    if org_id is None:
        return PaginatedResponse(
            data=[], meta=PaginationMeta(page=page, page_size=page_size, total=0, pages=0)
        )
    skip = (page - 1) * page_size
    query = select(Student).where(Student.organization_id == org_id)
    if class_id:
        query = query.join(ClassEnrollment, ClassEnrollment.student_id == Student.id).where(
            ClassEnrollment.class_id == _to_uuid(class_id),
            ClassEnrollment.status == "active",
        )
    if search:
        like = f"%{search}%"
        query = query.join(User, User.id == Student.user_id).where(
            or_(User.full_name.ilike(like), User.email.ilike(like), Student.student_number.ilike(like))
        )
    if status_filter:
        query = query.where(Student.status == status_filter)
    # total count via separate query
    from sqlalchemy import func

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return PaginatedResponse(
        data=[StudentOut.model_validate(o) for o in rows],
        meta=PaginationMeta(page=page, page_size=page_size, total=total, pages=(total + page_size - 1) // page_size),
    )


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    org_id = _to_uuid(payload.organization_id)
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or org_id not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of that organization")
    # ensure user exists
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = await db.execute(
        select(Student).where(Student.student_number == payload.student_number, Student.organization_id == org_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student number already exists")
    obj = await repo.create(payload, organization_id=org_id)
    return StudentOut.model_validate(obj)


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    obj = await repo.get(UUID(student_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(obj.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    return StudentOut.model_validate(obj)


@router.patch("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: str,
    payload: StudentUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    obj = await repo.get(UUID(student_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(obj.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    updated = await repo.update(UUID(student_id), payload)
    return StudentOut.model_validate(updated)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: str,
    current_user=Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    ok = await repo.delete(UUID(student_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return None
