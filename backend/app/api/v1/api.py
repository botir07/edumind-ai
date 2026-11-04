"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.v1.routers.academic import router as academic_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.organizations import router as organizations_router
from app.api.v1.routers.gradebook import router as gradebook_router
from app.api.v1.routers.homework import router as homework_router
from app.api.v1.routers.timetable import router as timetable_router
from app.api.v1.routers.attendance import router as attendance_router
from app.api.v1.routers.materials import router as materials_router
from app.api.v1.routers.notifications import router as notifications_router
from app.api.v1.routers.analytics import router as analytics_router
from app.ai_core.api import router as ai_core_router
from app.modules.ai_tutor import router as ai_tutor_router
from app.modules.ai_knowledge_map import router as ai_knowledge_map_router
from app.modules.ai_error_analysis import router as ai_error_analysis_router
from app.modules.ai_adaptive_learning import router as ai_adaptive_learning_router
from app.modules.ai_analytics import router as ai_analytics_router
from app.modules.ai_learning_paths import router as ai_learning_paths_router
from app.api.v1.routers.parents import router as parents_router
from app.api.v1.routers.students import router as students_router
from app.api.v1.routers.teachers import router as teachers_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(academic_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(parents_router)
api_router.include_router(gradebook_router)
api_router.include_router(homework_router)
api_router.include_router(timetable_router)
api_router.include_router(attendance_router)
api_router.include_router(materials_router)
api_router.include_router(notifications_router)
api_router.include_router(analytics_router)
api_router.include_router(ai_core_router)
api_router.include_router(ai_tutor_router)
api_router.include_router(ai_knowledge_map_router)
api_router.include_router(ai_error_analysis_router)
api_router.include_router(ai_adaptive_learning_router)
api_router.include_router(ai_learning_paths_router)
api_router.include_router(ai_analytics_router)

__all__ = ["api_router"]
