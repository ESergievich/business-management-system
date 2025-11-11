from fastapi import APIRouter

from app.api.api_v1.auth import router as auth_router
from app.core.config import settings

router = APIRouter(prefix=settings.api.v1.prefix)

router.include_router(auth_router)
