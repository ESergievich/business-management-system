from fastapi import APIRouter

from app.authentication.fastapi_users_object import fastapi_users
from app.core.config import settings
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["Users"],
)

# /me
# /{id}
router.include_router(
    router=fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
)
