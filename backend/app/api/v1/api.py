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

__all__ = ["api_router"]
