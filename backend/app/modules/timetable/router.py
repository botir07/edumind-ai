"""Timetable API routes (rooms + lessons)."""
from datetime import time as dtime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.class_ import Class
from app.models.lesson import Lesson
from app.models.room import Room
from app.models.teacher import Teacher
from app.repositories.base import CRUDRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.timetable import LessonCreate, LessonOut, LessonUpdate, RoomCreate, RoomOut, RoomUpdate

router = APIRouter(prefix="/timetable", tags=["timetable"])


def _to_uuid(value) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(value)


def _parse_time(value) -> Optional[dtime]:
    if value is None:
        return None
    if isinstance(value, dtime):
        return value
    return dtime.fromisoformat(value)


async def _member_org_ids(current_user, db: AsyncSession):
    if current_user.get("is_superuser"):
        return None
    memberships = await get_active_memberships(current_user, db)
    return [str(m.organization_id) for m in memberships]


# ---------- Rooms ----------
@router.get("/rooms", response_model=list[RoomOut])
async def list_rooms(
    organization_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(Room, db)
    org_id = _to_uuid(organization_id)
    if org_id is None:
        allowed = await _member_org_ids(current_user, db)
        org_id = _to_uuid(allowed[0]) if allowed else None
    if org_id is None:
        return []
    rows = await repo.get_multi(organization_id=org_id)
    return [RoomOut.model_validate(o) for o in rows]


@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    repo = CRUDRepository(Room, db)
    if not current_user.get("is_superuser"):
        allowed = await _member_org_ids(current_user, db)
        if not allowed or str(payload.organization_id) not in [str(o) for o in allowed]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of that organization")
    obj = await repo.create(payload)
    return RoomOut.model_validate(obj)


# ---------- Lessons ----------
def _overlap(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


@router.get("/lessons", response_model=list[LessonOut])
async def list_lessons(
    class_id: Optional[str] = Query(None),
    teacher_id: Optional[str] = Query(None),
    day_of_week: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lesson)
    if class_id:
        query = query.where(Lesson.class_id == _to_uuid(class_id))
    if teacher_id:
        query = query.where(Lesson.teacher_id == _to_uuid(teacher_id))
    if day_of_week is not None:
        query = query.where(Lesson.day_of_week == day_of_week)
    result = await db.execute(query)
    return [LessonOut.model_validate(o) for o in result.scalars().all()]


@router.post("/lessons", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    payload: LessonCreate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
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
    start_t = _parse_time(payload.start_time)
    end_t = _parse_time(payload.end_time)
    # simpler: check teacher overlap and room overlap separately
    teacher_conflict = await db.execute(
        select(Lesson).where(
            Lesson.day_of_week == payload.day_of_week,
            Lesson.teacher_id == payload.teacher_id,
            Lesson.start_time < end_t,
            start_t < Lesson.end_time,
        )
    )
    if teacher_conflict.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Teacher already has a lesson at this time")
    if payload.room_id:
        room_conflict = await db.execute(
            select(Lesson).where(
                Lesson.day_of_week == payload.day_of_week,
                Lesson.room_id == payload.room_id,
                Lesson.start_time < end_t,
                start_t < Lesson.end_time,
            )
        )
        if room_conflict.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room already occupied at this time")
    obj = Lesson(
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
        room_id=payload.room_id,
        day_of_week=payload.day_of_week,
        start_time=_parse_time(payload.start_time),
        end_time=_parse_time(payload.end_time),
        academic_year_id=payload.academic_year_id,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return LessonOut.model_validate(obj)


@router.patch("/lessons/{lesson_id}", response_model=LessonOut)
async def update_lesson(
    lesson_id: str,
    payload: LessonUpdate,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(Lesson, UUID(lesson_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key in ("start_time", "end_time") and isinstance(value, str):
            value = dtime.fromisoformat(value)
        setattr(obj, key, value)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return LessonOut.model_validate(obj)


@router.post("/lessons/{lesson_id}/cancel", response_model=LessonOut)
async def cancel_lesson(
    lesson_id: str,
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(Lesson, UUID(lesson_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    obj.is_cancelled = True
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return LessonOut.model_validate(obj)
