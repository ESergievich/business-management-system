"""Middleware for handling web authentication."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TokenFromCookieMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts JWT token from cookies and adds it to Authorization header.

    This allows web pages to work with tokens stored in cookies instead of LocalStorage.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and add token to headers if found in cookies."""
        # Get token from cookie
        token = request.cookies.get("access_token")

        # If token exists in cookie and not already in headers, add it
        if token and not request.headers.get("Authorization"):
            # Create mutable headers
            new_headers = list(request.scope["headers"])
            new_headers.append((b"authorization", f"Bearer {token}".encode()))
            request.scope["headers"] = new_headers

        return await call_next(request)
