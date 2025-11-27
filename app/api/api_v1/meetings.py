from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.fastapi_users_object import current_active_user
from app.core.config import settings
from app.core.db_helper import db_helper
from app.models import Meeting
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate,
    MeetingRead,
)
from app.service.meeting_service import MeetingService

router = APIRouter(prefix=settings.api.v1.meetings, tags=["Meetings"])


@router.post(
    "/",
    response_model=MeetingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new meeting",
)
async def create_meeting(
    meeting_data: MeetingCreate,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Meeting:
    """
    Create a new meeting.

    - **title**: Title of the meeting
    - **description**: Optional description
    - **start_time**: Start time (ISO 8601 format)
    - **end_time**: End time (ISO 8601 format)
    - **team_id**: ID of the team
    - **participant_ids**: List of participant user IDs

    The meeting will be checked for time conflicts with existing meetings
    for all participants.
    """
    service = MeetingService(session)
    return await service.create_meeting(meeting_data, current_user.id)


@router.get(
    "/{meeting_id}",
    response_model=MeetingRead,
    summary="Get meeting by ID",
)
async def get_meeting(
    meeting_id: int,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Meeting:
    """
    Get a specific meeting by ID.

    Only participants and the organizer can view the meeting.
    """
    service = MeetingService(session)
    return await service.get_meeting(meeting_id, current_user.id)


@router.get(
    "/",
    response_model=list[MeetingRead],
    summary="Get user's meetings",
)
async def get_user_meetings(
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    start_date: Annotated[datetime | None, Query(description="Filter meetings starting from this date")] = None,
    end_date: Annotated[datetime | None, Query(description="Filter meetings up to this date")] = None,
) -> list[Meeting]:
    """
    Get all meetings for the current user.

    Optionally filter by date range using start_date and end_date parameters.
    """
    service = MeetingService(session)
    return await service.get_user_meetings(current_user.id, start_date, end_date)


@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel meeting",
)
async def cancel_meeting(
    meeting_id: int,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> None:
    """
    Cancel (delete) a meeting.

    Only the organizer can cancel the meeting.
    """
    service = MeetingService(session)
    await service.cancel_meeting(meeting_id, current_user.id)
