from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.models import User
from app.models.access_token import AccessToken


async def get_user_from_cookie(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User | None:
    """
    Get user from access token cookie.

    Returns None if no token or invalid token.
    """
    if not access_token:
        return None

    try:
        # Find token in database
        result = await session.execute(
            select(AccessToken).where(AccessToken.token == access_token),
        )
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            return None

        # Get user
        user = await session.get(User, token_obj.user_id)

        if not user or not user.is_active:
            return None

        return user  # noqa: TRY300

    except Exception:  # noqa: BLE001
        return None


async def require_auth(
    _request: Request,
    user: Annotated[User | None, Depends(get_user_from_cookie)],
) -> User:
    """
    Require authentication for web routes.

    Raises 401 if not authenticated, which will be caught by error handler.
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return user
