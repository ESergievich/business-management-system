from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Meeting, Task, Team, User
from app.models.task import TaskStatus
from app.service.calendar_service import CalendarService


class TestCalendarService:
    """Tests for CalendarService methods."""

    def test_get_period_day(self) -> None:
        """Test day period calculation."""
        test_date = date(2024, 1, 15)
        start, end = CalendarService.get_period_day(test_date)

        assert start == datetime(2024, 1, 15, 0, 0, 0)
        assert end == datetime(2024, 1, 16, 0, 0, 0)
        assert (end - start).days == 1

    def test_get_period_month(self) -> None:
        """Test month period calculation."""
        test_date = date(2024, 2, 15)  # February
        start, end = CalendarService.get_period_month(test_date)

        assert start == datetime(2024, 2, 1, 0, 0, 0)
        assert end == datetime(2024, 3, 1, 0, 0, 0)
        assert start.month == 2
        assert end.month == 3

    def test_get_period_month_december(self) -> None:
        """Test month period calculation for December."""
        test_date = date(2024, 12, 15)
        start, end = CalendarService.get_period_month(test_date)

        assert start == datetime(2024, 12, 1, 0, 0, 0)
        assert end == datetime(2025, 1, 1, 0, 0, 0)

    @pytest.mark.asyncio
    async def test_get_meetings_for_period(
        self,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Test getting meetings within a period."""
        now = datetime.now()

        # Meeting within period
        meeting1 = Meeting(
            title="Meeting 1",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )

        # Meeting outside period
        meeting2 = Meeting(
            title="Meeting 2",
            start_time=now + timedelta(days=10),
            end_time=now + timedelta(days=10, hours=1),
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )

        test_session.add_all([meeting1, meeting2])
        await test_session.commit()

        service = CalendarService(test_session)
        meetings = await service.get_meetings_for_period(
            user_id=manager_user.id,
            start=now,
            end=now + timedelta(days=5),
        )

        assert len(meetings) == 1
        assert meetings[0].id == meeting1.id

    @pytest.mark.asyncio
    async def test_get_tasks_for_period(
        self,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Test getting tasks within a period."""
        now = datetime.now()

        # Task with deadline in period
        task1 = Task(
            title="Task 1",
            deadline=now + timedelta(days=2),
            team_id=team_with_members.id,
            creator_id=manager_user.id,
            status=TaskStatus.OPEN,
        )

        # Task with deadline outside period
        task2 = Task(
            title="Task 2",
            deadline=now + timedelta(days=10),
            team_id=team_with_members.id,
            creator_id=manager_user.id,
            status=TaskStatus.OPEN,
        )

        # Task without deadline (should be included if not completed)
        task3 = Task(
            title="Task 3",
            deadline=None,
            team_id=team_with_members.id,
            creator_id=manager_user.id,
            status=TaskStatus.IN_PROGRESS,
        )

        # Completed task without deadline (should be excluded)
        task4 = Task(
            title="Task 4",
            deadline=None,
            team_id=team_with_members.id,
            creator_id=manager_user.id,
            status=TaskStatus.COMPLETED,
        )

        test_session.add_all([task1, task2, task3, task4])
        await test_session.commit()

        service = CalendarService(test_session)
        tasks = await service.get_tasks_for_period(
            user_id=manager_user.id,
            start=now,
            end=now + timedelta(days=5),
        )

        task_ids = [t.id for t in tasks]
        assert task1.id in task_ids
        assert task2.id not in task_ids
        assert task3.id in task_ids  # No deadline, not completed
        assert task4.id not in task_ids  # Completed

    @pytest.mark.asyncio
    async def test_get_event_start_time(
        self,
        test_session: AsyncSession,
        team: Team,
        manager_user: User,
    ) -> None:
        """Test getting event start time for tasks and meetings."""
        now = datetime.now()

        # Task with deadline
        task_with_deadline = Task(
            title="Task",
            deadline=now + timedelta(days=1),
            team_id=team.id,
            creator_id=manager_user.id,
        )

        # Task without deadline
        task_without_deadline = Task(
            title="Task",
            deadline=None,
            team_id=team.id,
            creator_id=manager_user.id,
        )

        # Meeting
        meeting = Meeting(
            title="Meeting",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
            team_id=team.id,
            organizer_id=manager_user.id,
        )

        test_session.add_all([task_with_deadline, task_without_deadline, meeting])
        await test_session.commit()
        await test_session.refresh(task_without_deadline)

        # Test start time extraction
        assert CalendarService.get_event_start_time(task_with_deadline) == task_with_deadline.deadline
        assert CalendarService.get_event_start_time(task_without_deadline) == task_without_deadline.created_at
        assert CalendarService.get_event_start_time(meeting) == meeting.start_time


class TestCalendarEndpoints:
    """Tests for calendar API endpoints."""

    @pytest.mark.asyncio
    async def test_get_calendar_events_by_day(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Test getting events for a specific day."""
        target_date = date.today()
        now = datetime.combine(target_date, datetime.min.time())

        # Create events for today
        task = Task(
            title="Today's Task",
            deadline=now + timedelta(hours=10),
            team_id=team_with_members.id,
            creator_id=manager_user.id,
        )

        meeting = Meeting(
            title="Today's Meeting",
            start_time=now + timedelta(hours=14),
            end_time=now + timedelta(hours=15),
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )

        test_session.add_all([task, meeting])
        await test_session.commit()

        response = await manager_client.post(
            "/v1/calendar/events",
            json={"day": target_date.isoformat()},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) >= 2
        event_types = [e["type"] for e in data["events"]]
        assert "task" in event_types
        assert "meeting" in event_types

    @pytest.mark.asyncio
    async def test_get_calendar_events_by_month(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Test getting events for a specific month."""
        target_date = date.today()

        # Create events in current month
        month_start = datetime(target_date.year, target_date.month, 1)

        task = Task(
            title="Month Task",
            deadline=month_start + timedelta(days=15),
            team_id=team_with_members.id,
            creator_id=manager_user.id,
        )

        test_session.add(task)
        await test_session.commit()

        response = await manager_client.post(
            "/v1/calendar/events",
            json={"month": target_date.isoformat()},
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "start_period" in data
        assert "end_period" in data

    @pytest.mark.asyncio
    async def test_get_calendar_events_by_range(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Test getting events for custom date range."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        response = await manager_client.post(
            "/v1/calendar/events",
            json={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    @pytest.mark.asyncio
    async def test_get_calendar_events_invalid_filter(
        self,
        manager_client: AsyncClient,
        manager_user: User,
    ) -> None:
        """Test validation of filter parameters."""
        # No filter specified
        response = await manager_client.post(
            "/v1/calendar/events",
            json={},
        )

        assert response.status_code == 422

        # Multiple filters specified
        response = await manager_client.post(
            "/v1/calendar/events",
            json={
                "day": date.today().isoformat(),
                "month": date.today().isoformat(),
            },
        )

        assert response.status_code == 422

        # Range with only start
        response = await manager_client.post(
            "/v1/calendar/events",
            json={
                "start": date.today().isoformat(),
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_today_events(
        self,
        manager_client: AsyncClient,
        manager_user: User,
    ) -> None:
        """Test shortcut endpoint for today's events."""
        response = await manager_client.get(
            "/v1/calendar/today",
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    @pytest.mark.asyncio
    async def test_get_this_month_events(
        self,
        manager_client: AsyncClient,
        manager_user: User,
    ) -> None:
        """Test shortcut endpoint for current month's events."""
        response = await manager_client.get(
            "/v1/calendar/this-month",
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data

    @pytest.mark.asyncio
    async def test_calendar_events_sorted(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Test that events are sorted chronologically."""
        now = datetime.now()

        # Create events in non-chronological order
        meeting2 = Meeting(
            title="Later Meeting",
            start_time=now + timedelta(hours=5),
            end_time=now + timedelta(hours=6),
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )

        task1 = Task(
            title="Early Task",
            deadline=now + timedelta(hours=2),
            team_id=team_with_members.id,
            creator_id=manager_user.id,
        )

        meeting1 = Meeting(
            title="Middle Meeting",
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )

        test_session.add_all([meeting2, task1, meeting1])
        await test_session.commit()

        response = await manager_client.post(
            "/v1/calendar/events",
            json={
                "start": now.date().isoformat(),
                "end": (now.date() + timedelta(days=1)).isoformat(),
            },
        )

        assert response.status_code == 200
        events = response.json()["events"]

        # Verify chronological order
        if len(events) >= 3:
            # Find our events
            titles = [e["title"] for e in events]
            early_idx = titles.index("Early Task")
            middle_idx = titles.index("Middle Meeting")
            later_idx = titles.index("Later Meeting")

            assert early_idx < middle_idx < later_idx
