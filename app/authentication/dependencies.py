from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase

from app.authentication.user_manager import UserManager
from app.core.db_helper import db_helper
from app.models.access_token import AccessToken
from app.models.user import User

if TYPE_CHECKING:
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase as SQLAlchemyUserDatabaseType
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_db(
    session: Annotated["AsyncSession", Depends(db_helper.session_getter)],
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, int], None]:
    yield SQLAlchemyUserDatabase(session, User)


async def get_access_tokens_db(
    session: Annotated["AsyncSession", Depends(db_helper.session_getter)],
) -> AsyncGenerator[SQLAlchemyAccessTokenDatabase[AccessToken], None]:
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)


async def get_user_manager(
    users_db: Annotated["SQLAlchemyUserDatabaseType[User, int]", Depends(get_user_db)],
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(users_db)
