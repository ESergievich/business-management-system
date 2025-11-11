# mypy: ignore-errors

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from fastapi_users.authentication.strategy import DatabaseStrategy

from app.authentication.dependencies import get_access_tokens_db
from app.core.config import settings

if TYPE_CHECKING:
    from fastapi_users.authentication.strategy.db import AccessTokenDatabase

    from app.models.access_token import AccessToken
    from app.models.user import User


def get_database_strategy(
    access_tokens_db: Annotated["AccessTokenDatabase[AccessToken]", Depends(get_access_tokens_db)],
) -> DatabaseStrategy["User", int, "AccessToken"]:
    return DatabaseStrategy(
        database=access_tokens_db,
        lifetime_seconds=settings.access_token.lifetime_seconds,
    )
