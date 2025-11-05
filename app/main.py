from api import router as api_router
from fastapi import FastAPI

app = FastAPI(title="Business management system API")

app.include_router(api_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Hello from business management system!"}
