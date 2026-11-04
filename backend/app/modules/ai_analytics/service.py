"""Learning Analytics service.

Computes real database aggregations for student, teacher, and parent analytics.
Missing information is distinguished from zero values (None vs 0).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.access_control.enforcement import AICoreEnforcer
from app.ai_core.core.exceptions import AINotFoundError
from app.ai_core.models.phase3_tables import (
    AIStudentKnowledgeState,
    AILearningAttempt,
    AILearningError,
    AILearningPath,
)
from app.models import (
    AssignmentSubmission,
    AttendanceRecord,
    Class,
    ClassEnrollment,
    Grade,
    Parent,
    Student,
    Teacher,
)

from app.modules.ai_analytics.schemas import (  # noqa: E402
    ParentAnalyticsOut,
    SchoolAnalyticsOut,
    StudentAnalyticsOut,
    TeacherAnalyticsOut,
)


class LearningAnalyticsService:
    """Service for learning analytics (real DB aggregations)."""

    def __init__(self, session: AsyncSession, enforcer: AICoreEnforcer):
        self.session = session
        self.enforcer = enforcer

    # ---------- student ----------

    async def student_analytics(
        self,
        *,
        student_id: UUID,
        organization_id: UUID,
    ) -> StudentAnalyticsOut:
        await self.enforcer.require_org_access(organization_id)
        student = await self.session.get(Student, student_id)
        if not student or student.organization_id != organization_id:
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Student not found in organization")

        # average score
        avg_result = await self.session.execute(
            select(func.avg(Grade.score)).where(Grade.student_id == student_id)
        )
        avg_score = avg_result.scalar_one_or_none()

        # grade count
        grade_count_result = await self.session.execute(
            select(func.count(Grade.id)).where(Grade.student_id == student_id)
        )
        grade_count = grade_count_result.scalar_one_or_none() or 0

        # attendance by status
        att_result = await self.session.execute(
            select(AttendanceRecord.status, func.count(AttendanceRecord.id))
            .where(AttendanceRecord.student_id == student_id)
            .group_by(AttendanceRecord.status)
        )
        attendance_by_status = {row[0]: row[1] for row in att_result.all()}

        # submission count
        sub_result = await self.session.execute(
            select(func.count(AssignmentSubmission.id)).where(
                AssignmentSubmission.student_id == student_id
            )
        )
        submission_count = sub_result.scalar_one_or_none() or 0

        # mastery by topic
        mastery_result = await self.session.execute(
            select(AIStudentKnowledgeState.topic_id, AIStudentKnowledgeState.mastery_score)
            .where(
                AIStudentKnowledgeState.student_id == student_id,
                AIStudentKnowledgeState.topic_id.is_not(None),
            )
        )
        mastery_by_topic = {
            str(row[0]): float(row[1]) for row in mastery_result.all() if row[0] is not None
        }

        # topics needing practice (mastery < 60)
        topics_needing_practice = [
            str(tid) for tid, score in mastery_result.all() if score is not None and float(score) < 60
        ]
        # re-query since mastery_result exhausted
        mastery_result2 = await self.session.execute(
            select(AIStudentKnowledgeState.topic_id, AIStudentKnowledgeState.mastery_score)
            .where(
                AIStudentKnowledgeState.student_id == student_id,
                AIStudentKnowledgeState.topic_id.is_not(None),
                AIStudentKnowledgeState.mastery_score < 60,
            )
        )
        topics_needing_practice = [
            str(row[0]) for row in mastery_result2.all() if row[0] is not None
        ]

        # recent errors
        err_result = await self.session.execute(
            select(AILearningError.error_type, AILearningError.question, AILearningError.explanation)
            .where(AILearningError.student_id == student_id)
            .order_by(AILearningError.created_at.desc())
            .limit(5)
        )
        recent_errors = [
            {"error_type": row[0], "question": row[1], "explanation": row[2]}
            for row in err_result.all()
        ]

        # active paths
        from app.ai_core.models.phase3_tables import AILearningPath
        paths_result = await self.session.execute(
            select(func.count(AILearningPath.id)).where(
                AILearningPath.student_id == student_id,
                AILearningPath.status == "active",
            )
        )
        active_paths = paths_result.scalar_one_or_none() or 0

        return StudentAnalyticsOut(
            student_id=student_id,
            organization_id=organization_id,
            average_score=float(avg_score) if avg_score is not None else None,
            grade_count=grade_count,
            attendance_by_status=attendance_by_status,
            submission_count=submission_count,
            mastery_by_topic=mastery_by_topic,
            topics_needing_practice=topics_needing_practice,
            recent_errors=recent_errors,
            active_paths=active_paths,
            recommended_exercises=[],
        )

    # ---------- teacher ----------

    async def teacher_analytics(
        self,
        *,
        teacher_id: UUID,
        organization_id: UUID,
    ) -> TeacherAnalyticsOut:
        await self.enforcer.require_org_access(organization_id)
        teacher = await self.session.get(Teacher, teacher_id)
        if not teacher or teacher.organization_id != organization_id:
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Teacher not found in organization")

        # teacher's classes
        classes_result = await self.session.execute(
            select(Class).where(
                Class.organization_id == organization_id,
                Class.room_teacher_id == teacher_id,
            )
        )
        classes = classes_result.scalars().all()

        class_analytics: List[TeacherClassAnalyticsOut] = []
        total_students = 0
        all_scores: List[float] = []

        for klass in classes:
            # students in class
            enroll_result = await self.session.execute(
                select(ClassEnrollment).where(
                    ClassEnrollment.class_id == klass.id,
                    ClassEnrollment.status == "active",
                )
            )
            enrollments = enroll_result.scalars().all()
            student_ids = [e.student_id for e in enrollments]
            total_students += len(enrollments)

            # class average score
            if student_ids:
                class_avg_result = await self.session.execute(
                    select(func.avg(Grade.score)).where(Grade.student_id.in_(student_ids))
                )
                class_avg = class_avg_result.scalar_one_or_none()
                if class_avg is not None:
                    all_scores.append(float(class_avg))

            # mastery distribution for class
            mastery_result = await self.session.execute(
                select(AIStudentKnowledgeState.learning_status, func.count(AIStudentKnowledgeState.id))
                .where(
                    AIStudentKnowledgeState.student_id.in_(student_ids),
                    AIStudentKnowledgeState.learning_status.is_not(None),
                )
                .group_by(AIStudentKnowledgeState.learning_status)
            )
            mastery_dist = {row[0]: row[1] for row in mastery_result.all()}

            class_analytics.append(
                TeacherClassAnalyticsOut(
                    class_id=klass.id,
                    class_name=klass.name,
                    student_count=len(enrollments),
                    average_score=round(float(class_avg), 2) if class_avg is not None else None,
                    attendance_rate=None,
                    mastery_distribution=mastery_dist,
                    common_errors=[],
                    students_needing_help=[],
                )
            )

        overall_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else None

        return TeacherAnalyticsOut(
            teacher_id=teacher_id,
            organization_id=organization_id,
            classes=class_analytics,
            total_students=total_students,
            overall_average_score=overall_avg,
        )

    # ---------- parent ----------

    async def parent_analytics(
        self,
        *,
        parent_id: UUID,
        organization_id: UUID,
    ) -> ParentAnalyticsOut:
        await self.enforcer.require_org_access(organization_id)
        from app.models.parent import Parent
        from app.models.student_guardian import StudentGuardian

        parent = await self.session.get(Parent, parent_id)
        if not parent or parent.organization_id != organization_id:
            from app.ai_core.core.exceptions import AINotFoundError
            raise AINotFoundError("Parent not found in organization")

        # verified children
        guard_result = await self.session.execute(
            select(StudentGuardian).where(
                StudentGuardian.parent_id == parent_id,
                StudentGuardian.is_verified == True,  # noqa: E712
            )
        )
        guardians = guard_result.scalars().all()

        children: List[ParentChildAnalyticsOut] = []
        for g in guardians:
            student = await self.session.get(Student, g.student_id)
            if not student:
                continue
            # student analytics (reuse)
            student_analytics = await self.student_analytics(
                student_id=student.id, organization_id=organization_id
            )
            children.append(
                ParentChildAnalyticsOut(
                    student_id=student.id,
                    student_name=student.user.full_name if student.user else None,
                    student_number=student.student_number,
                    average_score=student_analytics.average_score,
                    attendance_rate=None,
                    mastery_by_topic=student_analytics.mastery_by_topic,
                    recent_errors=student_analytics.recent_errors,
                    recommended_exercises=[],
                )
            )

        return ParentAnalyticsOut(
            parent_id=parent_id,
            organization_id=organization_id,
            children=children,
        )
