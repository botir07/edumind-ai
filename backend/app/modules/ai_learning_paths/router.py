"""Learning Paths API routes (/api/v1/ai/learning-paths/*).

Manages personalized learning paths with ordered steps and progress tracking.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models import Student

from .schemas import (
    LearningPathCreate,
    LearningPathOut,
    LearningPathStepCreate,
    LearningPathStepOut,
    LearningPathStepComplete,
    LearningPathUpdate,
)
from .service import LearningPathsService

router = APIRouter(prefix="/ai/learning-paths", tags=["ai_learning_paths"])


def _build_service(db: AsyncSession, enforcer) -> LearningPathsService:
    return LearningPathsService(session=db, enforcer=enforcer)


async def _get_student(db: AsyncSession, current_user: dict) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student not found")
    return student


from sqlalchemy import select  # noqa: E402


@router.post("", response_model=LearningPathOut, status_code=status.HTTP_201_CREATED)
async def create_path(
    payload: LearningPathCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    await enforcer.require_org_access(student.organization_id)
    service = LearningPathsService(session=db, enforcer=enforcer)
    path = await service.create_path(
        student_id=student.id,
        organization_id=student.organization_id,
        title=payload.title,
        subject_id=payload.subject_id,
        target_topic_id=payload.target_topic_id,
        difficulty=payload.difficulty,
        steps=[s.model_dump() for s in payload.steps],
        objectives=None,
    )
    return await _path_out(service, path, student.id)


@router.get("", response_model=List[LearningPathOut])
async def list_paths(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
    status_filter: Optional[str] = Query(None),
):
    student = await _get_student(db, current_user)
    await enforcer.require_org_access(student.organization_id)
    service = LearningPathsService(session=db, enforcer=enforcer)
    paths = await service.list_paths(
        student_id=student.id, organization_id=student.organization_id,
        status_filter=status_filter,
    )
    return [await _path_out(service, p, student.id) for p in paths]


@router.get("/{path_id}", response_model=LearningPathOut)
async def get_path(
    path_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = LearningPathsService(session=db, enforcer=enforcer)
    path = await service.get_path(path_id=path_id, student_id=student.id)
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")
    return await _path_out(service, path, student.id)


@router.patch("/{path_id}", response_model=LearningPathOut)
async def update_path(
    path_id: UUID,
    payload: LearningPathUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = LearningPathsService(session=db, enforcer=enforcer)
    path = await service.update_path(
        path_id=path_id, student_id=student.id,
        title=payload.title, difficulty=payload.difficulty, status=payload.status,
    )
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")
    return await _path_out(service, path, student.id)


@router.delete("/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_path(
    path_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = LearningPathsService(session=db, enforcer=enforcer)
    ok = await service.delete_path(path_id=path_id, student_id=student.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")
    return None


@router.post("/{path_id}/steps/{step_id}/complete", response_model=LearningPathStepOut)
async def complete_step(
    path_id: UUID,
    step_id: UUID,
    payload: LearningPathStepComplete,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = LearningPathsService(session=db, enforcer=enforcer)
    step = await service.complete_step(
        path_id=path_id, step_id=step_id, student_id=student.id, score=payload.score,
    )
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found")
    return LearningPathStepOut.model_validate(step)


@router.get("/{path_id}/objectives")
async def list_objectives(
    path_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = LearningPathsService(session=db, enforcer=enforcer)
    objectives = await service.list_objectives(path_id=path_id, student_id=student.id)
    return [
        {"id": str(o.id), "objective": o.objective, "is_achieved": o.is_achieved,
         "achieved_at": o.achieved_at.isoformat() if o.achieved_at else None}
        for o in objectives
    ]


@router.post("/{path_id}/objectives/{objective_id}/achieve")
async def achieve_objective(
    path_id: UUID,
    objective_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = LearningPathsService(session=db, enforcer=enforcer)
    ok = await service.mark_objective_achieved(
        path_id=path_id, objective_id=objective_id, student_id=student.id
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objective not found")
    return {"status": "achieved"}


async def _path_out(
    service: LearningPathsService, path: Any, student_id: UUID
) -> LearningPathOut:
    # reload with steps to ensure fresh
    full = await service.get_path(path_id=path.id, student_id=student_id)
    return LearningPathOut(
        id=full.id,
        student_id=full.student_id,
        organization_id=full.organization_id,
        subject_id=full.subject_id,
        target_topic_id=full.target_topic_id,
        title=full.title,
        difficulty=full.difficulty,
        status=full.status,
        progress=float(full.progress),
        created_at=full.created_at,
        updated_at=full.updated_at,
        steps=[
            LearningPathStepOut(
                id=s.id,
                path_id=s.path_id,
                step_number=s.step_number,
                step_type=s.step_type,
                title=s.title,
                description=s.description,
                topic_id=s.topic_id,
                is_required=s.is_required,
                is_completed=s.is_completed,
                completed_at=s.completed_at,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in (full.steps or [])
        ],
    )
