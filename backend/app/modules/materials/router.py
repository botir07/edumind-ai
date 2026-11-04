"""Learning materials API routes."""
import os
import uuid as uuid_module
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.learning_material import LearningMaterial
from app.models.organization import Organization
from app.repositories.base import CRUDRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.materials import MaterialCreate, MaterialOut, MaterialUpdate

router = APIRouter(prefix="/materials", tags=["materials"])

MAX_UPLOAD_SIZE = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".txt", ".ppt", ".pptx"}


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


@router.get("", response_model=list[MaterialOut])
async def list_materials(
    organization_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(LearningMaterial)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    if org_id is not None:
        query = query.where(LearningMaterial.organization_id == org_id)
    else:
        # non-superuser with no org: return nothing
        if not current_user.get("is_superuser"):
            return []
    if subject_id:
        query = query.where(LearningMaterial.subject_id == _to_uuid(subject_id))
    if is_published is not None:
        query = query.where(LearningMaterial.is_published == is_published)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return [MaterialOut.model_validate(o) for o in result.scalars().all()]


@router.post("", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def create_material(
    payload: MaterialCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    org_id = _to_uuid(payload.organization_id)
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or str(org_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of that organization")
    repo = CRUDRepository(LearningMaterial, db)
    obj = await repo.create(payload, author_id=current_user["id"], organization_id=org_id)
    return MaterialOut.model_validate(obj)


@router.patch("/{material_id}", response_model=MaterialOut)
async def update_material(
    material_id: str,
    payload: MaterialUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(LearningMaterial, db)
    obj = await repo.get(UUID(material_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if str(obj.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")
    updated = await repo.update(UUID(material_id), payload)
    return MaterialOut.model_validate(updated)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: str,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(LearningMaterial, db)
    ok = await repo.delete(UUID(material_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return None


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_material(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if file.size and file.size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")
    safe_name = f"{uuid_module.uuid4().hex}_{os.path.basename(file.filename or 'file')}"
    storage_path = f"uploads/materials/{safe_name}"
    return {"storage_path": storage_path, "filename": safe_name, "mime_type": file.content_type, "size": file.size}


@router.get("/{material_id}/download")
async def download_material(material_id: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = CRUDRepository(LearningMaterial, db)
    obj = await repo.get(UUID(material_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    # controlled access: private storage path not exposed directly
    return {"storage_path": obj.file_path, "download_url": f"/api/v1/materials/{material_id}/file"}
