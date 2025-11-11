from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from api import router as api_router
from fastapi import FastAPI

from app.core.db_helper import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    yield
    await db_helper.dispose()


app = FastAPI(title="Business management system API", lifespan=lifespan)

app.include_router(api_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Hello from business management system!"}
