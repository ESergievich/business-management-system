from datetime import datetime

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import ConfigDict

from app.models.user import UserRole


class UserRead(BaseUser[int]):
    username: str
    role: UserRole = UserRole.USER
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseUserCreate):
    username: str


class UserAdminCreate(UserCreate):
    role: UserRole = UserRole.ADMIN


class UserUpdate(BaseUserUpdate):
    username: str | None = None
