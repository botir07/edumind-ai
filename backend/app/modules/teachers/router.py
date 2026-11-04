"""Teacher API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.organization import Organization
from app.models.teacher import Teacher
from app.models.user import User
from app.repositories.base import CRUDRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.teachers import TeacherCreate, TeacherOut, TeacherUpdate

router = APIRouter(prefix="/teachers", tags=["teachers"])


def _repo(db: AsyncSession) -> CRUDRepository:
    return CRUDRepository(Teacher, db)


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


@router.get("", response_model=PaginatedResponse[TeacherOut])
async def list_teachers(
    organization_id: Optional[str] = Query(None),
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
    query = select(Teacher).where(Teacher.organization_id == org_id)
    if search:
        like = f"%{search}%"
        query = query.join(User, User.id == Teacher.user_id).where(
            or_(User.full_name.ilike(like), User.email.ilike(like), Teacher.employee_number.ilike(like))
        )
    if status_filter:
        query = query.where(Teacher.status == status_filter)
    from sqlalchemy import func

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return PaginatedResponse(
        data=[TeacherOut.model_validate(o) for o in rows],
        meta=PaginationMeta(page=page, page_size=page_size, total=total, pages=(total + page_size - 1) // page_size),
    )


@router.post("", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    payload: TeacherCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    org_id = _to_uuid(payload.organization_id)
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or org_id not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of that organization")
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = await db.execute(
        select(Teacher).where(Teacher.employee_number == payload.employee_number, Teacher.organization_id == org_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee number already exists")
    obj = await repo.create(payload, organization_id=org_id)
    return TeacherOut.model_validate(obj)


@router.get("/{teacher_id}", response_model=TeacherOut)
async def get_teacher(
    teacher_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    obj = await repo.get(UUID(teacher_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(obj.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    return TeacherOut.model_validate(obj)


@router.patch("/{teacher_id}", response_model=TeacherOut)
async def update_teacher(
    teacher_id: str,
    payload: TeacherUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    obj = await repo.get(UUID(teacher_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(obj.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    updated = await repo.update(UUID(teacher_id), payload)
    return TeacherOut.model_validate(updated)


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    teacher_id: str,
    current_user=Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    ok = await repo.delete(UUID(teacher_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return None
