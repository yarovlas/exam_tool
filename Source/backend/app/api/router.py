from fastapi import APIRouter, Depends

from app.api.routes.exam_planning import router as exam_planning_router
from app.api.routes.exam_assessor import router as exam_assessor_router
from app.api.routes.assessor import router as assessor_router
from app.api.routes.auth import router as auth_router
from app.api.routes.student import router as student_router
from app.api.routes.exam_student import router as exam_student_router
from app.api.routes.health import router as health_router
from app.api.routes.opdracht_maker import router as opdracht_maker_router
from app.api.routes.product import router as product_router
from app.api.routes.assignment import router as assignment_router
from app.core.auth import get_current_user
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix=settings.api_prefix)
api_router.include_router(exam_student_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
api_router.include_router(exam_assessor_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
api_router.include_router(exam_planning_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
api_router.include_router(assessor_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
api_router.include_router(student_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
api_router.include_router(product_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
api_router.include_router(assignment_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
api_router.include_router(opdracht_maker_router, prefix=settings.api_prefix, dependencies=[Depends(get_current_user)])
