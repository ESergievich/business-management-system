from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router as api_router
from app.core.db_helper import db_helper
from app.errors.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
        yield
        await db_helper.dispose()

    app = FastAPI(title="Business management system API", lifespan=lifespan)

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/")
    def read_root() -> dict[str, str]:
        return {"message": "Hello from business management system!"}

    return app
