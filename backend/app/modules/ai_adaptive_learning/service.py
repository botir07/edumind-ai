"""Adaptive Learning service.

Generates explainable learning recommendations based on:
  - Knowledge Map mastery states
  - Error Analysis (frequent/repeated errors)
  - Learning Attempts (success rate, difficulty)

All recommendations carry a documented reason. No random recommendations.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.cache.service import CacheService
from app.ai_core.core.exceptions import AINotFoundError
from app.ai_core.models.phase3_tables import (
    AIAdaptiveRecommendation,
    AIStudentKnowledgeState,
    AILearningAttempt,
    AILearningError,
)
from app.models.student import Student


class AdaptiveLearningService:
    """Service for adaptive learning recommendations."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        enforcer: AICoreEnforcer,
        cache: Optional[CacheService] = None,
    ):
        self.session = session
        self.enforcer = enforcer
        self.cache = cache

    # ---------- recommendation generation ----------

    async def generate_recommendations(
        self,
        *,
        student_id: UUID,
        organization_id: UUID,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """Generate adaptive recommendations for a student.

        Each recommendation carries a documented reason.
        """
        await self.enforcer.require_org_access(organization_id)

        # Cache check
        cache_key = f"recs:{student_id}"
        if not force_refresh and self.cache:
            cached = await self.cache.get(str(organization_id), "adaptive_recs", cache_key)
            if cached:
                import json
                return json.loads(cached)

        # Fetch data
        mastery_states = await self.session.execute(
            select(AIStudentKnowledgeState).where(
                AIStudentKnowledgeState.student_id == student_id,
                AIStudentKnowledgeState.organization_id == organization_id,
            )
        )
        states = mastery_states.scalars().all()

        attempts = await self.session.execute(
            select(AILearningAttempt).where(
                AILearningAttempt.student_id == student_id,
                AILearningAttempt.organization_id == organization_id,
            ).order_by(AILearningAttempt.answered_at.desc()).limit(100)
        )
        attempt_list = attempts.scalars().all()

        errors = await self.session.execute(
            select(AILearningError).where(
                AILearningError.student_id == student_id,
                AILearningError.organization_id == organization_id,
            ).order_by(AILearningError.created_at.desc()).limit(100)
        )
        error_list = errors.scalars().all()

        now = datetime.now(timezone.utc)
        recommendations: List[Dict[str, Any]] = []

        # Build topic -> error count map
        topic_error_counts: Dict[Optional[UUID], int] = {}
        topic_error_types: Dict[Optional[UUID], List[str]] = {}
        for e in error_list:
            topic_error_counts[e.topic_id] = topic_error_counts.get(e.topic_id, 0) + 1
            topic_error_types.setdefault(e.topic_id, []).append(e.error_type)

        # Rule 1: Frequent errors in a topic → simpler_explanation
        for state in states:
            if state.topic_id and topic_error_counts.get(state.topic_id, 0) >= 2:
                recommendations.append({
                    "recommendation_type": "simpler_explanation",
                    "title": f"Soddaroq tushuntirish: {state.topic_id}",
                    "description": f"Siz bu mavzuga doimiy xato qilyapsiz. Soddaroq tushuntirish kerak.",
                    "reason": f"Doimiy xatolar soni: {topic_error_counts[state.topic_id]}",
                    "priority": 3,
                    "subject_id": str(state.subject_id) if state.subject_id else None,
                    "topic_id": str(state.topic_id) if state.topic_id else None,
                })

        # Rule 2: Same error repeated → error_analysis
        for topic_id, types in topic_error_types.items():
            if len(types) > 1 and types.count(types[0]) == len(types) and len(types) >= 2:
                recommendations.append({
                    "recommendation_type": "error_analysis",
                    "title": "Takrorlanuvchi xatoni tahlil qiling",
                    "description": "Bir xil xatoni takrorlamoqdasiz. Xatoni tahlil qilamiz.",
                    "reason": f"Takrorlanuvchi xato: {types[0]}",
                    "priority": 4,
                    "topic_id": str(topic_id) if topic_id else None,
                })

        # Rule 3: Simple tasks solved successfully → harder_practice
        easy_correct = [
            a for a in attempt_list
            if a.is_correct and a.difficulty in ("easy", None)
        ]
        if len(easy_correct) >= 3:
            # recommend harder practice for the most-attempted topic
            best_topic = None
            best_count = 0
            for a in attempt_list:
                if a.is_correct and a.topic_id:
                    topic_error_counts[a.topic_id] = topic_error_counts.get(a.topic_id, 0) + 1
                    # count correct per topic
            # simpler: pick a mastered topic and advance
            for state in states:
                if float(state.mastery_score) >= 80 and state.topic_id:
                    recommendations.append({
                        "recommendation_type": "harder_practice",
                        "title": "Qiyinroq mashq",
                        "description": "Mavzuga mustahkam qildingiz. Qiyinroq mashqlarga o'ting.",
                        "reason": f"Mustahkamlik balli: {state.mastery_score}",
                        "priority": 2,
                        "topic_id": str(state.topic_id),
                    })
                    break

        # Rule 4: Topic not practiced for a while → repetition
        for state in states:
            if state.last_practiced_at:
                days = (now - state.last_practiced_at.replace(tzinfo=timezone.utc)).days
                if days >= 7 and float(state.mastery_score) >= 40:
                    recommendations.append({
                        "recommendation_type": "repetition",
                        "title": "Takrorlash kerak",
                        "description": f"Bu mavzuga {days} kun berilmagan. Takrorlash tavsiya etiladi.",
                        "reason": f"Oxirgi mashqlash: {days} kun oldin",
                        "priority": 2,
                        "topic_id": str(state.topic_id) if state.topic_id else None,
                    })

        # Rule 5: Topic mastered → advance
        for state in states:
            if float(state.mastery_score) >= 80 and state.topic_id:
                recommendations.append({
                    "recommendation_type": "advance",
                    "title": "Keyingi mavzuga o'ting",
                    "description": "Bu mavzuga mustahkam qildingiz. Qo'shimcha mavzuga o'ting.",
                    "reason": f"Mustahkamlik balli: {state.mastery_score} (>=80)",
                    "priority": 1,
                    "topic_id": str(state.topic_id),
                })

        # Deduplicate by (type, topic)
        seen = set()
        unique: List[Dict[str, Any]] = []
        for r in recommendations:
            key = (r["recommendation_type"], r.get("topic_id"))
            if key not in seen:
                seen.add(key)
                unique.append(r)

        # Sort by priority desc
        unique.sort(key=lambda r: r["priority"], reverse=True)

        # Persist new recommendations (only new ones not already stored)
        existing = await self.session.execute(
            select(AIAdaptiveRecommendation).where(
                AIAdaptiveRecommendation.student_id == student_id,
                AIAdaptiveRecommendation.is_accepted == False,  # noqa: E712
                AIAdaptiveRecommendation.is_dismissed == False,  # noqa: E712
            )
        )
        existing_keys = {
            (r.recommendation_type, str(r.topic_id)) for r in existing.scalars().all()
        }
        for r in unique:
            if (r["recommendation_type"], r.get("topic_id")) not in existing_keys:
                rec = AIAdaptiveRecommendation(
                    student_id=student_id,
                    organization_id=organization_id,
                    recommendation_type=r["recommendation_type"],
                    title=r["title"],
                    description=r["description"],
                    subject_id=r.get("subject_id"),
                    topic_id=UUID(r["topic_id"]) if r.get("topic_id") else None,
                    reason=r["reason"],
                    priority=r["priority"],
                    is_accepted=False,
                    is_dismissed=False,
                )
                self.session.add(rec)
        await self.session.commit()

        # Cache
        if self.cache:
            import json
            await self.cache.set(
                str(organization_id), "adaptive_recs", cache_key,
                json.dumps(unique), ttl_seconds=300
            )

        return unique

    async def list_recommendations(
        self,
        *,
        student_id: UUID,
        organization_id: UUID,
        include_accepted_dismissed: bool = False,
    ) -> List[Dict[str, Any]]:
        await self.enforcer.require_org_access(organization_id)
        query = select(AIAdaptiveRecommendation).where(
            AIAdaptiveRecommendation.student_id == student_id,
            AIAdaptiveRecommendation.organization_id == organization_id,
        )
        if not include_accepted_dismissed:
            query = query.where(
                AIAdaptiveRecommendation.is_accepted == False,  # noqa: E712
                AIAdaptiveRecommendation.is_dismissed == False,  # noqa: E712
            )
        query = query.order_by(AIAdaptiveRecommendation.priority.desc(), AIAdaptiveRecommendation.created_at.desc())
        result = await self.session.execute(query)
        recs = result.scalars().all()
        return [
            {
                "id": r.id,
                "recommendation_type": r.recommendation_type,
                "title": r.title,
                "description": r.description,
                "subject_id": str(r.subject_id) if r.subject_id else None,
                "topic_id": str(r.topic_id) if r.topic_id else None,
                "reason": r.reason,
                "priority": r.priority,
                "is_accepted": r.is_accepted,
                "is_dismissed": r.is_dismissed,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in recs
        ]

    async def accept_recommendation(
        self,
        *,
        recommendation_id: UUID,
        student_id: UUID,
        organization_id: UUID,
    ) -> bool:
        await self.enforcer.require_org_access(organization_id)
        result = await self.session.execute(
            select(AIAdaptiveRecommendation).where(
                AIAdaptiveRecommendation.id == recommendation_id,
                AIAdaptiveRecommendation.student_id == student_id,
            )
        )
        rec = result.scalar_one_or_none()
        if not rec:
            return False
        rec.is_accepted = True
        rec.is_dismissed = False
        self.session.add(rec)
        await self.session.commit()
        return True

    async def dismiss_recommendation(
        self,
        *,
        recommendation_id: UUID,
        student_id: UUID,
        organization_id: UUID,
    ) -> bool:
        await self.enforcer.require_org_access(organization_id)
        result = await self.session.execute(
            select(AIAdaptiveRecommendation).where(
                AIAdaptiveRecommendation.id == recommendation_id,
                AIAdaptiveRecommendation.student_id == student_id,
            )
        )
        rec = result.scalar_one_or_none()
        if not rec:
            return False
        rec.is_dismissed = True
        rec.is_accepted = False
        self.session.add(rec)
        await self.session.commit()
        return True

    @staticmethod
    def algorithm_docs() -> Dict[str, Any]:
        """Return documentation of the adaptive decision rules."""
        return {
            "rules": [
                {
                    "condition": "Frequent errors in a topic (>=2)",
                    "action": "Offer simpler explanation",
                    "type": "simpler_explanation",
                },
                {
                    "condition": "Same error repeated",
                    "action": "Offer error-analysis breakdown",
                    "type": "error_analysis",
                },
                {
                    "condition": "Simple tasks solved successfully (>=3)",
                    "action": "Gradually increase difficulty",
                    "type": "harder_practice",
                },
                {
                    "condition": "Topic not practiced for >=7 days",
                    "action": "Offer repetition",
                    "type": "repetition",
                },
                {
                    "condition": "Topic mastered (mastery >= 80)",
                    "action": "Advance to next related topic",
                    "type": "advance",
                },
            ],
            "note": "All recommendations carry a documented reason. No random recommendations.",
        }
