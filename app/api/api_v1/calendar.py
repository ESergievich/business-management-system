from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.authentication.fastapi_users_object import current_active_user
from app.core.config import settings
from app.core.db_helper import db_helper
from app.models import Task, User
from app.models.meeting import Meeting
from app.schemas.calendar import CalendarEventRead, DateFilter, MeetingEventRead, TaskEventRead
from app.service.calendar_service import CalendarService

router = APIRouter(prefix=settings.api.v1.calendar, tags=["Calendar"])


def convert_event_to_schema(event: Task | Meeting) -> TaskEventRead | MeetingEventRead:
    """
    Convert a Task or Meeting model to its corresponding schema.

    Args:
        event: Task or Meeting instance from database

    Returns:
        TaskEventRead for tasks, MeetingEventRead for meetings
    """
    if isinstance(event, Task):
        return TaskEventRead(
            type="task",
            id=event.id,
            title=event.title,
            description=event.description,
            status=event.status.value,
            deadline=event.deadline,
            team_id=event.team_id,
            creator_id=event.creator_id,
            assignee_id=event.assignee_id,
            created_at=event.created_at,
        )

    return MeetingEventRead(
        type="meeting",
        id=event.id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        team_id=event.team_id,
        organizer_id=event.organizer_id,
        participant_ids=[p.id for p in event.participants],
    )


@router.post(
    "/events",
    status_code=status.HTTP_200_OK,
    summary="Get calendar events for a period",
    description=(
        "Retrieve all events (tasks and meetings) for the authenticated user "
        "within a specified time period. You can filter by:\n\n"
        "- **day**: Get events for a specific day\n"
        "- **month**: Get events for a specific month\n"
        "- **start + end**: Get events for a custom date range\n\n"
        "Only one filtering option can be used at a time."
    ),
)
async def get_calendar_events(
    filter_data: DateFilter,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CalendarEventRead:
    service = CalendarService(session)

    period_type = filter_data.get_period_type()

    if period_type == "day":
        start, end = service.get_period_day(filter_data.day)  # type: ignore[arg-type]
    elif period_type == "month":
        start, end = service.get_period_month(filter_data.month)  # type: ignore[arg-type]
    else:
        start = datetime.combine(filter_data.start, datetime.min.time()).replace(tzinfo=UTC)  # type: ignore[arg-type]
        end = datetime.combine(filter_data.end, datetime.min.time()).replace(tzinfo=UTC)  # type: ignore[arg-type]

    events = await service.get_user_events_for_period(
        user_id=current_user.id,
        start=start,
        end=end,
    )

    event_schemas = [convert_event_to_schema(event) for event in events]

    return CalendarEventRead(
        start_period=start,
        end_period=end,
        events=event_schemas,
    )


@router.get(
    "/today",
    summary="Get today's events",
    description="Shortcut to get all events for today",
)
async def get_today_events(
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CalendarEventRead:
    filter_data = DateFilter(day=date.today())  # type: ignore[call-arg]
    return await get_calendar_events(filter_data, current_user, session)


@router.get(
    "/this-month",
    summary="Get this month's events",
    description="Shortcut to get all events for the current month",
)
async def get_this_month_events(
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> CalendarEventRead:
    filter_data = DateFilter(month=date.today())  # type: ignore[call-arg]
    return await get_calendar_events(filter_data, current_user, session)
