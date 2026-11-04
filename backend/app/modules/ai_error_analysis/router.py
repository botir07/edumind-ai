"""Error Analysis API routes (/api/v1/ai/error-analysis/*).

Analyzes student answers to determine error type and provide explanations +
practice exercises. Uses Phase 2 AI Core components. Does not fabricate
answers or change official grades.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.models.phase3_tables import AILearningError
from app.ai_core.security.audit import SecurityAuditor
from app.ai_core.security.output_validation import OutputValidator
from app.ai_core.security.pii import PIIScanner
from app.ai_core.system_prompt.engine import SystemPromptEngine
from app.core.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models import OrganizationMembership, Student, User

from .schemas import (
    ErrorAnalysisCreate,
    ErrorAnalysisOut,
    ErrorAnalysisRequest,
    ErrorCategoryOut,
)
from .service import ErrorAnalysisService

router = APIRouter(prefix="/ai/error-analysis", tags=["ai_error_analysis"])


def _build_service(db: AsyncSession, enforcer) -> ErrorAnalysisService:
    return ErrorAnalysisService(
        session=db,
        enforcer=enforcer,
        prompt_engine=SystemPromptEngine(),
        output_validator=OutputValidator(),
        pii_scanner=PIIScanner(),
        auditor=SecurityAuditor(),
    )


async def _is_staff(current_user: dict, db: AsyncSession) -> bool:
    result = await db.execute(
        select(OrganizationMembership.role).where(
            OrganizationMembership.user_id == current_user["id"],
            OrganizationMembership.is_active == True,  # noqa: E712
        )
    )
    roles = [row[0] for row in result.all()]
    return any(r in ("SUPER_ADMIN", "SCHOOL_ADMIN", "TEACHER") for r in roles)


# ---------- Error categories ----------

@router.get("/categories", response_model=List[ErrorCategoryOut])
async def list_error_categories(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    service = _build_service(db, enforcer)
    await service.ensure_default_categories()
    return [ErrorCategoryOut.model_validate(c) for c in await service.list_error_categories()]


# ---------- Analyze ----------

@router.post("", response_model=ErrorAnalysisOut, status_code=status.HTTP_201_CREATED)
async def analyze_error(
    payload: ErrorAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    # Determine the student being analyzed.
    student_id = None
    if payload.attempt_id:
        result = await db.execute(
            select(AILearningAttempt).where(AILearningAttempt.id == payload.attempt_id)
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
        student_id = attempt.student_id
    else:
        # No attempt: current user must be a student analyzing their own answer.
        result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
        student = result.scalars().first()
        print(f"DEBUG router: current_user={current_user}, student={student}, student.id={student.id if student else None}")
        print(f"DEBUG router RIGHT BEFORE CALL: student.id={student.id if student else None}, type={type(student.id) if student else None}")
        if not student:
            print(f"DEBUG: current_user={current_user}, student not found by user_id")
            # Fallback: look up student by email from current_user
            result = await db.execute(
                select(Student).join(User, Student.user_id == User.id).where(User.email == current_user["email"])
            )
            student = result.scalars().first()
            print(f"DEBUG: student by email={student}")
        if not student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can analyze without an attempt id",
            )

    student_obj = student or await db.get(Student, student_id)
    await enforcer.require_org_access(student_obj.organization_id)

    service = _build_service(db, enforcer)
    try:
        return await service.analyze(
            student_id=student.id,
            question=payload.question,
            student_answer=payload.student_answer,
            correct_answer=payload.correct_answer,
            topic_id=payload.topic_id,
            attempt_id=payload.attempt_id,
        )
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analysis failed")


# ---------- History ----------

@router.get("/history", response_model=List[ErrorAnalysisOut])
async def error_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student not found")
    await enforcer.require_org_access(student.organization_id)

    service = _build_service(db, enforcer)
    errors = await service.list_errors(
        student_id=student.id, organization_id=student.organization_id, limit=limit
    )
    return [ErrorAnalysisOut.model_validate(e) for e in errors]


@router.get("/{analysis_id}", response_model=ErrorAnalysisOut)
async def get_error_analysis(
    analysis_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    enforcer=Depends(get_ai_enforcer),
):
    result = await db.execute(select(AILearningError).where(AILearningError.id == analysis_id))
    error = result.scalar_one_or_none()
    if not error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    await enforcer.require_org_access(error.organization_id)

    result2 = await db.execute(select(Student).where(Student.user_id == current_user["id"]))
    student = result2.scalar_one_or_none()
    if student and student.id != error.student_id and not await _is_staff(current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your analysis")
    return ErrorAnalysisOut.model_validate(error)
