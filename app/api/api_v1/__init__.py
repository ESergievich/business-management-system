from fastapi import APIRouter

from app.api.api_v1.auth import router as auth_router
from app.api.api_v1.calendar import router as calendar_router
from app.api.api_v1.comments import router as comments_router
from app.api.api_v1.evaluations import router as evaluations_router
from app.api.api_v1.meetings import router as meetings_router
from app.api.api_v1.tasks import router as tasks_router
from app.api.api_v1.teams import router as teams_router
from app.api.api_v1.users import router as users_router
from app.core.config import settings

router = APIRouter(prefix=settings.api.v1.prefix)

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(teams_router)
router.include_router(comments_router)
router.include_router(evaluations_router)
router.include_router(tasks_router)
router.include_router(meetings_router)
router.include_router(calendar_router)
