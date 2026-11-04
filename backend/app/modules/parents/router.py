"""Parent and guardian API routes."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.parent import Parent
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.models.user import User
from app.repositories.base import CRUDRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.parents import GuardianCreate, GuardianOut, GuardianVerify, ParentCreate, ParentOut, ParentUpdate

router = APIRouter(prefix="/parents", tags=["parents"])


def _repo(db: AsyncSession) -> CRUDRepository:
    return CRUDRepository(Parent, db)


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


@router.get("", response_model=PaginatedResponse[ParentOut])
async def list_parents(
    organization_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
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
    query = select(Parent).where(Parent.organization_id == org_id)
    if search:
        like = f"%{search}%"
        query = query.join(User, User.id == Parent.user_id).where(
            or_(User.full_name.ilike(like), User.email.ilike(like))
        )
    from sqlalchemy import func

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    rows = result.scalars().all()
    return PaginatedResponse(
        data=[ParentOut.model_validate(o) for o in rows],
        meta=PaginationMeta(page=page, page_size=page_size, total=total, pages=(total + page_size - 1) // page_size),
    )


@router.post("", response_model=ParentOut, status_code=status.HTTP_201_CREATED)
async def create_parent(
    payload: ParentCreate,
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
    obj = await repo.create(payload, organization_id=org_id)
    return ParentOut.model_validate(obj)


@router.get("/{parent_id}", response_model=ParentOut)
async def get_parent(
    parent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(db)
    obj = await repo.get(UUID(parent_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found")
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(obj.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    return ParentOut.model_validate(obj)


@router.get("/{parent_id}/children")
async def list_parent_children(
    parent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # A parent may only see their own verified children.
    result = await db.execute(
        select(StudentGuardian, Student)
        .join(Student, Student.id == StudentGuardian.student_id)
        .where(StudentGuardian.parent_id == UUID(parent_id), StudentGuardian.is_verified == True)  # noqa: E712
    )
    rows = []
    for guardian, student in result.all():
        rows.append(
            {
                "guardian_id": str(guardian.id),
                "student_id": str(student.id),
                "student_number": student.student_number,
                "relationship": guardian.relationship,
            }
        )
    return rows


@router.post("/guardians", response_model=GuardianOut, status_code=status.HTTP_201_CREATED)
async def create_guardian(
    payload: GuardianCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(StudentGuardian, db)
    org_id = None
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of any organization")
        org_id = _to_uuid(allowed[0])
        student = await db.get(Student, payload.student_id)
        if not student or str(student.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student not in your organization")
    existing = await db.execute(
        select(StudentGuardian).where(
            StudentGuardian.student_id == payload.student_id,
            StudentGuardian.parent_id == payload.parent_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Guardian relationship already exists")
    obj = await repo.create(payload)
    return GuardianOut.model_validate(obj)


@router.patch("/guardians/{guardian_id}/verify", response_model=GuardianOut)
async def verify_guardian(
    guardian_id: str,
    payload: GuardianVerify,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(StudentGuardian, db)
    obj = await repo.get(UUID(guardian_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guardian not found")
    obj.is_verified = payload.is_verified
    obj.verified_by = current_user["id"]
    obj.verified_at = datetime.now(timezone.utc)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return GuardianOut.model_validate(obj)
