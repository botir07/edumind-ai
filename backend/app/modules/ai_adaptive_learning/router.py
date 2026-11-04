"""Adaptive Learning API routes (/api/v1/ai/recommendations/*).

Generates explainable learning recommendations based on knowledge map, errors,
and attempts. Uses Phase 2 AI Core Access Control + Cache.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.cache.service import CacheService
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models import Student

from .schemas import RecommendationOut, RecommendationsOut
from .service import AdaptiveLearningService

router = APIRouter(prefix="/ai/recommendations", tags=["ai_adaptive_learning"])

cache_service = CacheService()


def _build_service(db: AsyncSession, enforcer) -> AdaptiveLearningService:
    return AdaptiveLearningService(session=db, enforcer=enforcer, cache=cache_service)


async def _get_student(db: AsyncSession, current_user: dict) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student not found")
    return student


@router.get("", response_model=RecommendationsOut)
async def list_recommendations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
    force_refresh: bool = Query(False),
):
    student = await _get_student(db, current_user)
    await enforcer.require_org_access(student.organization_id)
    service = _build_service(db, enforcer)
    recs = await service.generate_recommendations(
        student_id=student.id, organization_id=student.organization_id, force_refresh=force_refresh
    )
    # Fetch persisted recommendations to return proper schema objects
    stored = await service.list_recommendations(
        student_id=student.id, organization_id=student.organization_id,
        include_accepted_dismissed=False,
    )
    return RecommendationsOut(
        recommendations=[
            RecommendationOut(
                id=r["id"],
                student_id=student.id,
                organization_id=student.organization_id,
                recommendation_type=r["recommendation_type"],
                title=r["title"],
                description=r.get("description"),
                subject_id=r.get("subject_id"),
                topic_id=r.get("topic_id"),
                reason=r["reason"],
                priority=r["priority"],
                is_accepted=r["is_accepted"],
                is_dismissed=r["is_dismissed"],
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
            )
            for r in stored
        ],
        algorithm_docs=AdaptiveLearningService.algorithm_docs(),
    )


@router.post("/{recommendation_id}/accept", response_model=RecommendationOut)
async def accept_recommendation(
    recommendation_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = _build_service(db, enforcer)
    ok = await service.accept_recommendation(
        recommendation_id=recommendation_id, student_id=student.id, organization_id=student.organization_id
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return await _get_single_recommendation(service, recommendation_id, student)


@router.post("/{recommendation_id}/dismiss", response_model=RecommendationOut)
async def dismiss_recommendation(
    recommendation_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    student = await _get_student(db, current_user)
    service = _build_service(db, enforcer)
    ok = await service.dismiss_recommendation(
        recommendation_id=recommendation_id, student_id=student.id, organization_id=student.organization_id
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return await _get_single_recommendation(service, recommendation_id, student)


@router.get("/algorithm", response_model=dict)
async def algorithm(current_user: dict = Depends(get_current_user)):
    return AdaptiveLearningService.algorithm_docs()


async def _get_single_recommendation(service: AdaptiveLearningService, recommendation_id: UUID, student: Student) -> RecommendationOut:
    recs = await service.list_recommendations(
        student_id=student.id, organization_id=student.organization_id,
        include_accepted_dismissed=True,
    )
    for r in recs:
        if r["id"] == recommendation_id:
            return RecommendationOut(
                id=r["id"], student_id=student.id, organization_id=student.organization_id,
                recommendation_type=r["recommendation_type"], title=r["title"],
                description=r.get("description"), subject_id=r.get("subject_id"),
                topic_id=r.get("topic_id"), reason=r["reason"], priority=r["priority"],
                is_accepted=r["is_accepted"], is_dismissed=r["is_dismissed"],
                created_at=r.get("created_at"), updated_at=r.get("updated_at"),
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
