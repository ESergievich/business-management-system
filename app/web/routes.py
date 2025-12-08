from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models import User
from app.web.dependencies import require_auth

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
API_URL = "/api"


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Home page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "api_url": API_URL},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Login page."""
    return templates.TemplateResponse("auth/login.html", {"request": request, "api_url": API_URL})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    """Registration page."""
    return templates.TemplateResponse("auth/register.html", {"request": request, "api_url": API_URL})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Annotated[User, Depends(require_auth)],
) -> HTMLResponse:
    """User dashboard."""
    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": current_user,
            "api_url": API_URL,
        },
    )


@router.get("/teams", response_class=HTMLResponse)
async def teams_page(
    request: Request,
    current_user: Annotated[User, Depends(require_auth)],
) -> HTMLResponse:
    """Teams management page."""
    return templates.TemplateResponse(
        "teams/index.html",
        {
            "request": request,
            "user": current_user,
            "api_url": API_URL,
        },
    )


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    current_user: Annotated[User, Depends(require_auth)],
) -> HTMLResponse:
    """Tasks page."""
    return templates.TemplateResponse(
        "tasks/index.html",
        {
            "request": request,
            "user": current_user,
            "api_url": API_URL,
        },
    )


@router.get("/meetings", response_class=HTMLResponse)
async def meetings_page(
    request: Request,
    current_user: Annotated[User, Depends(require_auth)],
) -> HTMLResponse:
    """Meetings page."""
    return templates.TemplateResponse(
        "meetings/index.html",
        {
            "request": request,
            "user": current_user,
            "api_url": API_URL,
        },
    )


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(
    request: Request,
    current_user: Annotated[User, Depends(require_auth)],
) -> HTMLResponse:
    """Calendar page."""
    return templates.TemplateResponse(
        "calendar/index.html",
        {
            "request": request,
            "user": current_user,
            "api_url": API_URL,
        },
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: Annotated[User, Depends(require_auth)],
) -> HTMLResponse:
    """User profile page."""
    return templates.TemplateResponse(
        "profile/index.html",
        {
            "request": request,
            "user": current_user,
            "api_url": API_URL,
        },
    )
