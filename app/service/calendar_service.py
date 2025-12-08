from calendar import monthrange
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Task
from app.models.meeting import Meeting
from app.models.task import TaskStatus


class CalendarService:
    """
    Service for calendar functionality.

    Provides methods to retrieve and organize tasks and meetings
    for different time periods (day, month, custom range).
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize calendar service.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.session = session

    @staticmethod
    def get_period_day(date_data: date) -> tuple[datetime, datetime]:
        """
        Get start and end datetime for a specific day.

        Args:
            date_data: The date to get period for

        Returns:
            Tuple of (start_datetime, end_datetime) where:
            - start_datetime: 00:00:00 of the specified day
            - end_datetime: 00:00:00 of the next day (exclusive)
        """
        start = datetime.combine(date_data, datetime.min.time()).replace(tzinfo=UTC)
        end = start + timedelta(days=1)
        return start, end

    @staticmethod
    def get_period_month(date_data: date) -> tuple[datetime, datetime]:
        """
        Get start and end datetime for a specific month.

        Args:
            date_data: Any date in the target month (day is ignored)

        Returns:
            Tuple of (start_datetime, end_datetime) where:
            - start_datetime: 00:00:00 of the first day of the month
            - end_datetime: 00:00:00 of the first day of next month (exclusive)
        """
        start = datetime(date_data.year, date_data.month, 1, 0, 0, 0, tzinfo=UTC)
        days_count = monthrange(date_data.year, date_data.month)[1]
        end = start.replace(day=days_count) + timedelta(days=1)
        return start, end

    async def get_meetings_for_period(
        self,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> list[Meeting]:
        """
        Get all meetings for a user within a time period.

        A meeting is included if it overlaps with the period in any way:
        - Starts within the period
        - Ends within the period
        - Spans the entire period

        Args:
            user_id: ID of the user
            start: Start of the period (inclusive)
            end: End of the period (exclusive)

        Returns:
            List of meetings sorted by start time
        """
        stmt = (
            select(Meeting)
            .options(selectinload(Meeting.participants))
            .join(Meeting.participants)
            .where(
                Meeting.participants.any(id=user_id),
                Meeting.start_time < end,
                Meeting.end_time >= start,
            )
            .order_by(Meeting.start_time)
        )

        result = await self.session.scalars(stmt)
        return list(result.unique())

    async def get_tasks_for_period(
        self,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> list[Task]:
        """
        Get all tasks for a user within a time period.

        Includes:
        - Tasks with deadlines in the period
        - Tasks without deadlines that are not completed (always shown)

        Args:
            user_id: ID of the user (creator or assignee)
            start: Start of the period (inclusive)
            end: End of the period (exclusive)

        Returns:
            List of tasks sorted by deadline (tasks without deadline first)
        """
        stmt = (
            select(Task)
            .where(
                or_(
                    Task.creator_id == user_id,
                    Task.assignee_id == user_id,
                ),
                or_(
                    and_(
                        Task.deadline.is_not(None),
                        Task.deadline >= start,
                        Task.deadline < end,
                    ),
                    and_(
                        Task.deadline.is_(None),
                        Task.status != TaskStatus.COMPLETED,
                    ),
                ),
            )
            .order_by(
                Task.deadline.is_(None),
                Task.deadline,
            )
        )

        result = await self.session.scalars(stmt)
        return list(result)

    @staticmethod
    def get_event_start_time(event: Task | Meeting) -> datetime:
        """
        Get the effective start time of an event.

        For tasks:
            - Returns deadline if set
            - Returns creation time if no deadline

        For meetings:
            - Returns start_time

        Args:
            event: Task or Meeting object

        Returns:
            Datetime representing when the event occurs/is due
        """
        dt = event.deadline or event.created_at if isinstance(event, Task) else event.start_time

        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        return dt

    async def get_user_events_for_period(
        self,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> list[Task | Meeting]:
        """
        Get all events (tasks and meetings) for a user within a time period.

        Combines tasks and meetings, then sorts them chronologically by their
        effective start time.

        Args:
            user_id: ID of the user
            start: Start of the period (inclusive)
            end: End of the period (exclusive)

        Returns:
            List of events sorted by start time/deadline
        """
        meetings = await self.get_meetings_for_period(user_id, start, end)
        tasks = await self.get_tasks_for_period(user_id, start, end)

        events: list[Task | Meeting] = [*meetings, *tasks]
        events.sort(key=self.get_event_start_time)

        return events
