"""Models package - imports all SQLAlchemy models so Alembic can detect them."""
# Import all modules here so Base.metadata is fully populated for autogenerate.
from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.organization_membership import OrganizationMembership  # noqa: F401
from app.models.user_session import UserSession  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.consent_record import ConsentRecord  # noqa: F401
from app.models.academic_year import AcademicYear  # noqa: F401
from app.models.grade_level import GradeLevel  # noqa: F401
from app.models.class_ import Class  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.topic import Topic  # noqa: F401
from app.models.curriculum_version import CurriculumVersion  # noqa: F401
from app.models.class_subject import ClassSubject  # noqa: F401
from app.models.class_enrollment import ClassEnrollment  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.parent import Parent  # noqa: F401
from app.models.student_guardian import StudentGuardian  # noqa: F401
from app.models.assessment import Assessment  # noqa: F401
from app.models.grade import Grade  # noqa: F401
from app.models.grade_history import GradeHistory  # noqa: F401
from app.models.room import Room  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.assignment import Assignment  # noqa: F401
from app.models.assignment_submission import AssignmentSubmission  # noqa: F401
from app.models.submission_file import SubmissionFile  # noqa: F401
from app.models.attendance_session import AttendanceSession  # noqa: F401
from app.models.attendance_record import AttendanceRecord  # noqa: F401
from app.models.learning_material import LearningMaterial  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.notification_preference import NotificationPreference  # noqa: F401
from app.ai_core.models.tables import (  # noqa: F401
    AIPromptTemplate,
    AIPromptVersion,
    AIDocument,
    AIDocumentChunk,
    AIEmbeddingMetadata,
    AIRetrievalLog,
    AIToolRegistry,
    AIToolExecutionLog,
    AIAccessPolicy,
    AISecurityEvent,
    AICacheMetadata,
    AITraceMetadata,
)
from app.ai_core.models.phase3_tables import (  # noqa: F401
    AITutorSession,
    AITutorMessage,
    AIKnowledgeSubject,
    AIKnowledgeTopic,
    AIKnowledgeSubtopic,
    AIKnowledgeSkill,
    AIStudentKnowledgeState,
    AILearningAttempt,
    AIErrorCategory,
    AILearningError,
    AIAdaptiveRecommendation,
    AILearningPath,
    AILearningPathStep,
    AILearningPathProgress,
    AILearningObjective,
    AIAnalyticsSnapshot,
)

__all__ = [
    "Organization",
    "User",
    "OrganizationMembership",
    "UserSession",
    "AuditLog",
    "ConsentRecord",
    "AcademicYear",
    "GradeLevel",
    "Class",
    "Subject",
    "Topic",
    "CurriculumVersion",
    "ClassSubject",
    "ClassEnrollment",
    "Student",
    "Teacher",
    "Parent",
    "StudentGuardian",
    "Assessment",
    "Grade",
    "GradeHistory",
    "Room",
    "Lesson",
    "Assignment",
    "AssignmentSubmission",
    "SubmissionFile",
    "AttendanceSession",
    "AttendanceRecord",
    "LearningMaterial",
    "Notification",
    "NotificationPreference",
    "AIPromptTemplate",
    "AIPromptVersion",
    "AIDocument",
    "AIDocumentChunk",
    "AIEmbeddingMetadata",
    "AIRetrievalLog",
    "AIToolRegistry",
    "AIToolExecutionLog",
    "AIAccessPolicy",
    "AISecurityEvent",
    "AICacheMetadata",
    "AITraceMetadata",
    "AITutorSession",
    "AITutorMessage",
    "AIKnowledgeSubject",
    "AIKnowledgeTopic",
    "AIKnowledgeSubtopic",
    "AIKnowledgeSkill",
    "AIStudentKnowledgeState",
    "AILearningAttempt",
    "AIErrorCategory",
    "AILearningError",
    "AIAdaptiveRecommendation",
    "AILearningPath",
    "AILearningPathStep",
    "AILearningPathProgress",
    "AILearningObjective",
    "AIAnalyticsSnapshot",
]
