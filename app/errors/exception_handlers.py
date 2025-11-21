from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.errors.exceptions import APIError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def api_exception_handler(_request: Request, exc: APIError) -> JSONResponse:
        error = exc.to_pydantic()
        return JSONResponse(
            status_code=exc.status_code,
            content=error.model_dump(),
        )
