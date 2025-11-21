from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends

from app.authentication.fastapi_users_object import current_active_user
from app.errors.exceptions import ForbiddenAccessError
from app.models import User

if TYPE_CHECKING:
    from app.models.user import UserRole


def role_required(*allowed_roles: "UserRole") -> Callable[["User"], Coroutine[Any, Any, User]]:
    """
    Dependency generator that checks if the current user has one of the allowed roles.

    Args:
        allowed_roles (UserRole): List of roles that are allowed to access the endpoint.

    Raises:
        ForbiddenAccess: If the current user's role is not in allowed_roles.

    Returns:
        Callable: A dependency function for FastAPI that validates the user's role.
    """

    async def verify_role(user: Annotated[User, Depends(current_active_user)]) -> "User":
        if allowed_roles and user.role not in allowed_roles:
            raise ForbiddenAccessError
        return user

    return verify_role
