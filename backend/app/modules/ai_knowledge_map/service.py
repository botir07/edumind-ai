"""Knowledge Map service.

Builds the subject -> topic -> subtopic -> skill hierarchy and computes
student mastery states transparently from real attempt data (not just school grades).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.dependencies import get_ai_enforcer
from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.models.phase3_tables import (
    AIKnowledgeSkill,
    AIKnowledgeSubject,
    AIKnowledgeSubtopic,
    AIKnowledgeTopic,
    AIStudentKnowledgeState,
)
from app.models.student import Student


class KnowledgeMapService:
    """Service for the knowledge map and student mastery states."""

    def __init__(self, session: AsyncSession, enforcer: AICoreEnforcer):
        self.session = session
        self.enforcer = enforcer

    # ---------- hierarchy CRUD (admin/teacher) ----------

    async def create_subject(
        self, *, organization_id: UUID, name: str, code: Optional[str] = None
    ) -> AIKnowledgeSubject:
        obj = AIKnowledgeSubject(
            organization_id=organization_id, name=name, code=code
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def list_subjects(self, organization_id: UUID) -> List[AIKnowledgeSubject]:
        result = await self.session.execute(
            select(AIKnowledgeSubject).where(
                AIKnowledgeSubject.organization_id == organization_id
            ).order_by(AIKnowledgeSubject.name)
        )
        return result.scalars().all()

    async def create_topic(
        self, *, subject_id: UUID, name: str, code: Optional[str] = None, order_index: int = 0
    ) -> AIKnowledgeTopic:
        obj = AIKnowledgeTopic(
            subject_id=subject_id, name=name, code=code, order_index=order_index
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def list_topics(self, subject_id: UUID) -> List[AIKnowledgeTopic]:
        result = await self.session.execute(
            select(AIKnowledgeTopic).where(
                AIKnowledgeTopic.subject_id == subject_id
            ).order_by(AIKnowledgeTopic.order_index, AIKnowledgeTopic.name)
        )
        return result.scalars().all()

    async def create_subtopic(
        self, *, topic_id: UUID, name: str, code: Optional[str] = None, order_index: int = 0
    ) -> AIKnowledgeSubtopic:
        obj = AIKnowledgeSubtopic(
            topic_id=topic_id, name=name, code=code, order_index=order_index
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def list_subtopics(self, topic_id: UUID) -> List[AIKnowledgeSubtopic]:
        result = await self.session.execute(
            select(AIKnowledgeSubtopic).where(
                AIKnowledgeSubtopic.topic_id == topic_id
            ).order_by(AIKnowledgeSubtopic.order_index, AIKnowledgeSubtopic.name)
        )
        return result.scalars().all()

    async def create_skill(
        self, *, subtopic_id: UUID, name: str, code: Optional[str] = None, order_index: int = 0
    ) -> AIKnowledgeSkill:
        obj = AIKnowledgeSkill(
            subtopic_id=subtopic_id, name=name, code=code, order_index=order_index
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def list_skills(self, subtopic_id: UUID) -> List[AIKnowledgeSkill]:
        result = await self.session.execute(
            select(AIKnowledgeSkill).where(
                AIKnowledgeSkill.subtopic_id == subtopic_id
            ).order_by(AIKnowledgeSkill.order_index, AIKnowledgeSkill.name)
        )
        return result.scalars().all()

    # ---------- mastery state ----------

    async def get_student_mastery(
        self, *, student_id: UUID, organization_id: UUID
    ) -> List[AIStudentKnowledgeState]:
        """Get all mastery states for a student in an org."""
        await self.enforcer.require_org_access(organization_id)
        result = await self.session.execute(
            select(AIStudentKnowledgeState).where(
                AIStudentKnowledgeState.student_id == student_id,
                AIStudentKnowledgeState.organization_id == organization_id,
            ).order_by(AIStudentKnowledgeState.updated_at.desc())
        )
        return result.scalars().all()

    async def get_mastery_state(
        self,
        *,
        student_id: UUID,
        organization_id: UUID,
        subject_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        subtopic_id: Optional[UUID] = None,
        skill_id: Optional[UUID] = None,
    ) -> Optional[AIStudentKnowledgeState]:
        """Get a specific mastery state."""
        await self.enforcer.require_org_access(organization_id)
        result = await self.session.execute(
            select(AIStudentKnowledgeState).where(
                AIStudentKnowledgeState.student_id == student_id,
                AIStudentKnowledgeState.organization_id == organization_id,
                AIStudentKnowledgeState.subject_id == subject_id,
                AIStudentKnowledgeState.topic_id == topic_id,
                AIStudentKnowledgeState.subtopic_id == subtopic_id,
                AIStudentKnowledgeState.skill_id == skill_id,
            )
        )
        return result.scalar_one_or_none()

    async def build_knowledge_map(
        self, *, student_id: UUID, organization_id: UUID
    ) -> Dict[str, Any]:
        """Build the full knowledge map for a student: hierarchy + mastery states.

        Mastery states are computed transparently from real attempt data
        (ai_learning_attempts), not just school grades.
        """
        await self.enforcer.require_org_access(organization_id)

        # Verify student belongs to org
        student = await self.session.get(Student, student_id)
        if not student or student.organization_id != organization_id:
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Student not found in organization")

        subjects = await self.list_subjects(organization_id)
        topics: List[AIKnowledgeTopic] = []
        subtopics: List[AIKnowledgeSubtopic] = []
        skills: List[AIKnowledgeSkill] = []
        for s in subjects:
            topics.extend(await self.list_topics(s.id))
        for t in topics:
            subtopics.extend(await self.list_subtopics(t.id))
        for st in subtopics:
            skills.extend(await self.list_skills(st.id))

        mastery_states = await self.get_student_mastery(
            student_id=student_id, organization_id=organization_id
        )

        # Return raw dicts; the router converts to Pydantic schemas.
        return {
            "subjects": [
                {
                    "id": str(s.id),
                    "organization_id": str(s.organization_id),
                    "name": s.name,
                    "code": s.code,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in subjects
            ],
            "topics": [
                {
                    "id": str(t.id),
                    "subject_id": str(t.subject_id),
                    "name": t.name,
                    "code": t.code,
                    "order_index": t.order_index,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in topics
            ],
            "subtopics": [
                {
                    "id": str(st.id),
                    "topic_id": str(st.topic_id),
                    "name": st.name,
                    "code": st.code,
                    "order_index": st.order_index,
                    "created_at": st.created_at.isoformat() if st.created_at else None,
                    "updated_at": st.updated_at.isoformat() if st.updated_at else None,
                }
                for st in subtopics
            ],
            "skills": [
                {
                    "id": str(k.id),
                    "subtopic_id": str(k.subtopic_id),
                    "name": k.name,
                    "code": k.code,
                    "order_index": k.order_index,
                    "created_at": k.created_at.isoformat() if k.created_at else None,
                    "updated_at": k.updated_at.isoformat() if k.updated_at else None,
                }
                for k in skills
            ],
            "mastery_states": [
                {
                    "id": str(m.id),
                    "student_id": str(m.student_id),
                    "organization_id": str(m.organization_id),
                    "subject_id": str(m.subject_id) if m.subject_id else None,
                    "topic_id": str(m.topic_id) if m.topic_id else None,
                    "subtopic_id": str(m.subtopic_id) if m.subtopic_id else None,
                    "skill_id": str(m.skill_id) if m.skill_id else None,
                    "mastery_score": float(m.mastery_score),
                    "confidence": float(m.confidence),
                    "attempt_count": m.attempt_count,
                    "correct_answers": m.correct_answers,
                    "incorrect_answers": m.incorrect_answers,
                    "last_practiced_at": m.last_practiced_at.isoformat() if m.last_practiced_at else None,
                    "last_assessed_at": m.last_assessed_at.isoformat() if m.last_assessed_at else None,
                    "learning_status": m.learning_status,
                    "evidence_references": m.evidence_references,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in mastery_states
            ],
        }

    @staticmethod
    def mastery_algorithm_docs() -> Dict[str, Any]:
        """Return documentation of the transparent mastery algorithm."""
        return {
            "algorithm": "weighted attempt-based mastery with recency",
            "mastery_score_range": [0, 100],
            "confidence_range": [0, 1],
            "score_change": {
                "correct": +2,
                "incorrect": -1,
                "bounds": [0, 100],
            },
            "confidence": "correct_answers / attempt_count",
            "status_thresholds": {
                "0": "NOT_STARTED",
                "<40": "LEARNING",
                "<60": "NEEDS_PRACTICE",
                "<80": "DEVELOPING",
                ">=80": "MASTERED",
            },
            "inputs": [
                "attempt_count",
                "correct_answers",
                "incorrect_answers",
                "last_practiced_at",
                "last_assessed_at",
            ],
            "note": "Mastery score is an estimate, not objective truth. Computed from real attempt data, not only school grades.",
        }
