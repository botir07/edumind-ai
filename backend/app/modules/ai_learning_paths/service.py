"""Learning Paths service.

Manages personalized learning paths: ordered steps toward a target topic,
with progress tracking. Paths are editable; steps whose knowledge is already
confirmed can be skipped.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.core.exceptions import AINotFoundError
from app.ai_core.models.phase3_tables import (
    AILearningObjective,
    AILearningPath,
    AILearningPathProgress,
    AILearningPathStep,
)
from app.models.student import Student


class LearningPathsService:
    """Service for personalized learning paths."""

    def __init__(self, session: AsyncSession, enforcer: AICoreEnforcer):
        self.session = session
        self.enforcer = enforcer

    # ---------- path CRUD ----------

    async def create_path(
        self,
        *,
        student_id: UUID,
        organization_id: UUID,
        title: str,
        subject_id: Optional[UUID] = None,
        target_topic_id: Optional[UUID] = None,
        difficulty: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        objectives: Optional[List[str]] = None,
    ) -> AILearningPath:
        await self.enforcer.require_org_access(organization_id)
        student = await self.session.get(Student, student_id)
        if not student or student.organization_id != organization_id:
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Student not found in organization")

        path = AILearningPath(
            student_id=student_id,
            organization_id=organization_id,
            subject_id=subject_id,
            target_topic_id=target_topic_id,
            title=title,
            difficulty=difficulty,
            status="active",
            progress=0.0,
        )
        self.session.add(path)
        await self.session.flush()
        await self.session.refresh(path)

        # steps
        step_number = 0
        for s in (steps or []):
            step_number += 1
            step = AILearningPathStep(
                path_id=path.id,
                step_number=step_number,
                step_type=s.get("step_type", "explanation"),
                title=s.get("title", f"Step {step_number}"),
                description=s.get("description"),
                topic_id=s.get("topic_id"),
                is_required=s.get("is_required", True),
                is_completed=False,
            )
            self.session.add(step)

        # objectives
        for i, obj in enumerate(objectives or []):
            self.session.add(AILearningObjective(
                path_id=path.id, objective=obj, is_achieved=False
            ))

        await self.session.flush()
        await self.session.refresh(path)
        return path

    async def list_paths(
        self,
        *,
        student_id: UUID,
        organization_id: UUID,
        status_filter: Optional[str] = None,
    ) -> List[AILearningPath]:
        await self.enforcer.require_org_access(organization_id)
        query = select(AILearningPath).where(
            AILearningPath.student_id == student_id,
            AILearningPath.organization_id == organization_id,
        )
        if status_filter:
            query = query.where(AILearningPath.status == status_filter)
        query = query.order_by(AILearningPath.updated_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_path(
        self,
        *,
        path_id: UUID,
        student_id: UUID,
    ) -> Optional[AILearningPath]:
        result = await self.session.execute(
            select(AILearningPath).where(
                AILearningPath.id == path_id,
                AILearningPath.student_id == student_id,
            )
        )
        path = result.scalar_one_or_none()
        if not path:
            return None
        await self.enforcer.require_org_access(path.organization_id)
        # load steps
        steps_result = await self.session.execute(
            select(AILearningPathStep).where(
                AILearningPathStep.path_id == path.id
            ).order_by(AILearningPathStep.step_number)
        )
        path.steps = steps_result.scalars().all()
        # load objectives
        obj_result = await self.session.execute(
            select(AILearningObjective).where(AILearningObjective.path_id == path.id)
        )
        path.objectives = obj_result.scalars().all()
        return path

    async def update_path(
        self,
        *,
        path_id: UUID,
        student_id: UUID,
        title: Optional[str] = None,
        difficulty: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[AILearningPath]:
        path = await self.get_path(path_id=path_id, student_id=student_id)
        if not path:
            return None
        if title is not None:
            path.title = title
        if difficulty is not None:
            path.difficulty = difficulty
        if status is not None:
            path.status = status
        self.session.add(path)
        await self.session.flush()
        await self.session.refresh(path)
        return path

    async def delete_path(
        self,
        *,
        path_id: UUID,
        student_id: UUID,
    ) -> bool:
        path = await self.get_path(path_id=path_id, student_id=student_id)
        if not path:
            return False
        await self.session.delete(path)
        await self.session.flush()
        return True

    # ---------- step completion ----------

    async def complete_step(
        self,
        *,
        path_id: UUID,
        step_id: UUID,
        student_id: UUID,
        score: Optional[float] = None,
    ) -> Optional[AILearningPathStep]:
        path = await self.get_path(path_id=path_id, student_id=student_id)
        if not path:
            return None
        step = await self.session.get(AILearningPathStep, step_id)
        if not step or step.path_id != path.id:
            return None
        step.is_completed = True
        step.completed_at = datetime.now(timezone.utc)
        self.session.add(step)

        # progress
        steps_result = await self.session.execute(
            select(AILearningPathStep).where(AILearningPathStep.path_id == path.id)
        )
        steps = steps_result.scalars().all()
        if steps:
            completed = sum(1 for s in steps if s.is_completed)
            path.progress = round((completed / len(steps)) * 100, 2)
            if path.progress >= 100:
                path.status = "completed"
        self.session.add(path)

        # progress record
        self.session.add(AILearningPathProgress(
            path_id=path.id,
            step_id=step.id,
            student_id=student_id,
            organization_id=path.organization_id,
            status="completed",
            score=score,
            completed_at=datetime.now(timezone.utc),
        ))

        await self.session.flush()
        await self.session.refresh(step)
        return step

    # ---------- objectives ----------

    async def list_objectives(
        self,
        *,
        path_id: UUID,
        student_id: UUID,
    ) -> List[AILearningObjective]:
        path = await self.get_path(path_id=path_id, student_id=student_id)
        if not path:
            return []
        result = await self.session.execute(
            select(AILearningObjective).where(AILearningObjective.path_id == path.id)
        )
        return result.scalars().all()

    async def mark_objective_achieved(
        self,
        *,
        path_id: UUID,
        objective_id: UUID,
        student_id: UUID,
    ) -> bool:
        path = await self.get_path(path_id=path_id, student_id=student_id)
        if not path:
            return False
        result = await self.session.execute(
            select(AILearningObjective).where(
                AILearningObjective.id == objective_id,
                AILearningObjective.path_id == path.id,
            )
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.is_achieved = True
        obj.achieved_at = datetime.now(timezone.utc)
        self.session.add(obj)
        await self.session.flush()
        return True
