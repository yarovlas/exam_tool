from fastapi import APIRouter

from app.api.routes.email import router as email_router
from app.api.routes.exam_planning import router as exam_planning_router
from app.api.routes.health import router as health_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(exam_planning_router, prefix=settings.api_prefix)
api_router.include_router(email_router, prefix=settings.api_prefix)
