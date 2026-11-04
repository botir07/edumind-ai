"""Organizations API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.organization import Organization
from app.models.organization_membership import OrganizationMembership
from app.repositories.base import CRUDRepository
from app.schemas.academic import AcademicYearOut
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.organization import OrganizationCreate, OrganizationOut, OrganizationUpdate

router = APIRouter(prefix="/organizations", tags=["organizations"])


def repo(db: AsyncSession = Depends(get_db)) -> CRUDRepository:
    return CRUDRepository(Organization, db)


@router.get("", response_model=PaginatedResponse[OrganizationOut])
async def list_organizations(
    r=Depends(repo),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    organization_id: Optional[str] = Query(None),
):
    # Non-superusers see only organizations they are members of.
    skip = (page - 1) * page_size
    if not current_user.get("is_superuser"):
        memberships = await get_active_memberships(current_user, r.session)
        org_ids = [str(m.organization_id) for m in memberships]
        if organization_id and organization_id not in org_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
        if not org_ids:
            return PaginatedResponse(data=[], meta=PaginationMeta(page=page, page_size=page_size, total=0, pages=0))
        # filter by membership orgs
        query = None  # placeholder; CRUD base filters by single org_id
        total = len(org_ids)
        rows = []
        for oid in org_ids:
            org = await r.get(UUID(oid))
            if org:
                rows.append(org)
        rows = rows[skip : skip + page_size]
        return PaginatedResponse(
            data=[OrganizationOut.model_validate(o) for o in rows],
            meta=PaginationMeta(page=page, page_size=page_size, total=total, pages=(total + page_size - 1) // page_size),
        )
    total = await r.count(organization_id=organization_id)
    rows = await r.get_multi(organization_id=organization_id, skip=skip, limit=page_size)
    return PaginatedResponse(
        data=[OrganizationOut.model_validate(o) for o in rows],
        meta=PaginationMeta(page=page, page_size=page_size, total=total, pages=(total + page_size - 1) // page_size),
    )


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    r=Depends(repo),
):
    existing = await r.session.execute(
        select(Organization).where(Organization.code == payload.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization code already exists")
    org = await r.create(payload)
    return OrganizationOut.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: str,
    current_user=Depends(get_current_user),
    r=Depends(repo),
):
    org = await r.get(UUID(org_id))
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if not current_user.get("is_superuser"):
        memberships = await get_active_memberships(current_user, r.session)
        if str(org.id) not in [str(m.organization_id) for m in memberships]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    return OrganizationOut.model_validate(org)


@router.patch("/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    r=Depends(repo),
):
    org = await r.get(UUID(org_id))
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    if not current_user.get("is_superuser"):
        memberships = await get_active_memberships(current_user, r.session)
        if str(org.id) not in [str(m.organization_id) for m in memberships]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    updated = await r.update(UUID(org_id), payload)
    return OrganizationOut.model_validate(updated)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    current_user=Depends(require_role("SUPER_ADMIN")),
    r=Depends(repo),
):
    ok = await r.delete(UUID(org_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return None


@router.get("/{org_id}/memberships")
async def list_memberships(
    org_id: str,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.user import User

    result = await db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(OrganizationMembership.organization_id == UUID(org_id))
    )
    rows = []
    for membership, user in result.all():
        rows.append(
            {
                "id": str(membership.id),
                "user_id": str(user.id),
                "user_email": user.email,
                "user_full_name": user.full_name,
                "role": membership.role,
                "is_active": membership.is_active,
            }
        )
    return rows
