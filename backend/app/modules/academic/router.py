"""Academic structure API routes (years, grades, classes, subjects, topics, curricula)."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.academic_year import AcademicYear
from app.models.class_ import Class
from app.models.curriculum_version import CurriculumVersion
from app.models.grade_level import GradeLevel
from app.models.subject import Subject
from app.models.topic import Topic
from app.repositories.base import CRUDRepository
from app.schemas.academic import (
    AcademicYearCreate,
    AcademicYearOut,
    AcademicYearUpdate,
    ClassCreate,
    ClassOut,
    ClassUpdate,
    CurriculumVersionCreate,
    CurriculumVersionOut,
    CurriculumVersionUpdate,
    GradeLevelCreate,
    GradeLevelOut,
    GradeLevelUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
    TopicCreate,
    TopicOut,
    TopicUpdate,
)

router = APIRouter(prefix="/academic", tags=["academic"])


def _repo(model, db: AsyncSession) -> CRUDRepository:
    return CRUDRepository(model, db)


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


async def _resolve_org_id(current_user, db: AsyncSession, payload) -> Optional[UUID]:
    org_id = getattr(payload, "organization_id", None) if payload else None
    if org_id is not None:
        return _to_uuid(org_id)
    if current_user.get("is_superuser"):
        return None
    allowed = await _member_org_ids(current_user, db)
    return _to_uuid(allowed[0]) if allowed else None


def _list_response(rows, out_schema):
    return [out_schema.model_validate(o) for o in rows]


# ---------- Academic Years ----------
@router.get("/academic-years", response_model=list[AcademicYearOut])
async def list_academic_years(
    organization_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(AcademicYear, db)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    rows = await repo.get_multi(organization_id=org_id, skip=skip, limit=limit)
    return _list_response(rows, AcademicYearOut)


@router.post("/academic-years", response_model=AcademicYearOut, status_code=status.HTTP_201_CREATED)
async def create_academic_year(
    payload: AcademicYearCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(AcademicYear, db)
    org_id = await _resolve_org_id(current_user, db, payload)
    if not current_user.get("is_superuser") and org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of any organization")
    obj = await repo.create(payload, organization_id=org_id)
    return AcademicYearOut.model_validate(obj)


# ---------- Grade Levels ----------
@router.get("/grade-levels", response_model=list[GradeLevelOut])
async def list_grade_levels(
    organization_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(GradeLevel, db)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    rows = await repo.get_multi(organization_id=org_id, skip=skip, limit=limit)
    return _list_response(rows, GradeLevelOut)


@router.post("/grade-levels", response_model=GradeLevelOut, status_code=status.HTTP_201_CREATED)
async def create_grade_level(
    payload: GradeLevelCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(GradeLevel, db)
    org_id = await _resolve_org_id(current_user, db, payload)
    if not current_user.get("is_superuser") and org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of any organization")
    obj = await repo.create(payload, organization_id=org_id)
    return GradeLevelOut.model_validate(obj)


# ---------- Classes ----------
@router.get("/classes", response_model=list[ClassOut])
async def list_classes(
    organization_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(Class, db)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    rows = await repo.get_multi(organization_id=org_id, skip=skip, limit=limit)
    return _list_response(rows, ClassOut)


@router.post("/classes", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: ClassCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(Class, db)
    org_id = await _resolve_org_id(current_user, db, payload)
    if not current_user.get("is_superuser") and org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of any organization")
    obj = await repo.create(payload, organization_id=org_id)
    return ClassOut.model_validate(obj)


# ---------- Subjects ----------
@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(
    organization_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(Subject, db)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    rows = await repo.get_multi(organization_id=org_id, skip=skip, limit=limit)
    return _list_response(rows, SubjectOut)


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(Subject, db)
    org_id = await _resolve_org_id(current_user, db, payload)
    if not current_user.get("is_superuser") and org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of any organization")
    obj = await repo.create(payload, organization_id=org_id)
    return SubjectOut.model_validate(obj)


# ---------- Topics ----------
@router.get("/topics", response_model=list[TopicOut])
async def list_topics(
    organization_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(Topic, db)
    filters = {"subject_id": _to_uuid(subject_id)} if subject_id else None
    rows = await repo.get_multi(organization_id=None, skip=skip, limit=limit, filters=filters)
    return _list_response(rows, TopicOut)


@router.post("/topics", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
async def create_topic(
    payload: TopicCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(Topic, db)
    obj = await repo.create(payload)
    return TopicOut.model_validate(obj)


# ---------- Curriculum Versions ----------
@router.get("/curriculum-versions", response_model=list[CurriculumVersionOut])
async def list_curriculum_versions(
    organization_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(CurriculumVersion, db)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    rows = await repo.get_multi(organization_id=org_id, skip=skip, limit=limit)
    return _list_response(rows, CurriculumVersionOut)


@router.post(
    "/curriculum-versions", response_model=CurriculumVersionOut, status_code=status.HTTP_201_CREATED
)
async def create_curriculum_version(
    payload: CurriculumVersionCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = _repo(CurriculumVersion, db)
    org_id = await _resolve_org_id(current_user, db, payload)
    if not current_user.get("is_superuser") and org_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of any organization")
    obj = await repo.create(payload, organization_id=org_id)
    return CurriculumVersionOut.model_validate(obj)
