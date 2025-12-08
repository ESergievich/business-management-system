from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from app.admin.admin import setup_admin
from app.api import router as api_router
from app.core.config import settings
from app.core.db_helper import db_helper
from app.errors.exception_handlers import register_exception_handlers
from app.web.middleware import TokenFromCookieMiddleware
from app.web.routes import router as web_router


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
        yield
        await db_helper.dispose()

    app = FastAPI(
        title="Business management system API",
        lifespan=lifespan,
        description="Modern business management system with teams, tasks, meetings and evaluations",
        version="1.0.0",
    )

    # Add session middleware for admin panel
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.access_token.reset_password_token_secret,
    )

    # Add token from cookie middleware for web routes
    app.add_middleware(TokenFromCookieMiddleware)

    # Setup admin panel
    setup_admin(app, db_helper.engine)

    # Register error handlers
    register_exception_handlers(app)

    # Add custom 401 handler for web routes
    @app.exception_handler(401)
    async def redirect_to_login(
        request: Request,
        _exc: StarletteHTTPException,
    ) -> JSONResponse | RedirectResponse:
        """Redirect to login page on 401 for web routes."""
        if request.url.path.startswith("/api/"):
            # For API routes, return JSON
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
            )
        # For web routes, redirect to login
        return RedirectResponse(url=f"/login?next={request.url.path}")

    # Include routers
    app.include_router(api_router)
    app.include_router(web_router)

    return app


app = create_app()
