import logging

from fastapi import Request
from fastapi_users import BaseUserManager, IntegerIDMixin

from app.core.config import settings
from app.models.user import User

log = logging.getLogger(__name__)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.access_token.reset_password_token_secret
    verification_token_secret = settings.access_token.verification_token_secret

    async def on_after_register(
        self,
        user: User,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        """Send user a confirmation e-mail when their account is created."""
        log.warning("User %r has registered.", user.id)

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        """Send user a verification e-mail when their account is created."""
        log.warning(
            "Verification requested for user %r. Verification token: %r",
            user.id,
            token,
        )

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        """Send user a password reset e-mail when their password is forgotten."""
        log.warning(
            "User %r has forgot their password. Reset token: %r",
            user.id,
            token,
        )
