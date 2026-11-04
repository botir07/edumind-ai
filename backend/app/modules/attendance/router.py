"""Attendance API routes."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_active_memberships, get_current_user, require_role
from app.database.session import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_session import AttendanceSession
from app.models.class_ import Class
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.repositories.base import CRUDRepository
from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceRecordOut,
    AttendanceSessionCreate,
    AttendanceSessionOut,
)

router = APIRouter(prefix="/attendance", tags=["attendance"])


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


# ---------- Sessions ----------
@router.get("/sessions", response_model=list[AttendanceSessionOut])
async def list_sessions(
    class_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AttendanceSession)
    if class_id:
        query = query.where(AttendanceSession.class_id == _to_uuid(class_id))
    result = await db.execute(query)
    return [AttendanceSessionOut.model_validate(o) for o in result.scalars().all()]


@router.post("/sessions", response_model=AttendanceSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: AttendanceSessionCreate,
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
    obj = AttendanceSession(
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        teacher_id=current_user["id"],
        date=payload.session_date,
        academic_year_id=payload.academic_year_id,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return AttendanceSessionOut.model_validate(obj)


# ---------- Records ----------
@router.post("/sessions/{session_id}/records", response_model=list[AttendanceRecordOut], status_code=status.HTTP_201_CREATED)
async def mark_attendance(
    session_id: str,
    records: list[AttendanceRecordCreate],
    current_user=Depends(require_role("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER")),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(AttendanceSession, UUID(session_id))
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    allowed_statuses = {"present", "absent", "late", "excused"}
    out = []
    for rec in records:
        if rec.status not in allowed_statuses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attendance status")
        # upsert record
        existing = await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.session_id == UUID(session_id),
                AttendanceRecord.student_id == rec.student_id,
            )
        )
        obj = existing.scalar_one_or_none()
        if obj:
            obj.status = rec.status
            obj.note = rec.note
            obj.marked_by = current_user["id"]
            obj.marked_at = datetime.now(timezone.utc)
        else:
            obj = AttendanceRecord(
                session_id=UUID(session_id),
                student_id=rec.student_id,
                status=rec.status,
                note=rec.note,
                marked_by=current_user["id"],
                marked_at=datetime.now(timezone.utc),
            )
            db.add(obj)
        await db.flush()
        await db.refresh(obj)
        out.append(AttendanceRecordOut.model_validate(obj))
    return out


@router.get("/student/{student_id}", response_model=list[AttendanceRecordOut])
async def student_attendance(
    student_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AttendanceRecord)
        .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
        .where(AttendanceRecord.student_id == UUID(student_id))
    )
    result = await db.execute(query)
    return [AttendanceRecordOut.model_validate(o) for o in result.scalars().all()]
