from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Meeting, Team, User


class TestCreateMeeting:
    """Tests for POST /meetings endpoint."""

    @pytest.mark.asyncio
    async def test_create_meeting_success(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Can create meeting with valid data."""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)

        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Team Standup",
                "description": "Daily standup meeting",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [regular_user.id],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Team Standup"
        assert data["organizer_id"] == manager_user.id
        assert regular_user.id in data["participant_ids"]
        assert manager_user.id in data["participant_ids"]  # Auto-added

    @pytest.mark.asyncio
    async def test_create_meeting_invalid_time(
        self,
        manager_client: AsyncClient,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Cannot create meeting with end_time before start_time."""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time - timedelta(hours=1)

        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Meeting",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [],
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_meeting_participant_not_in_team(
        self,
        manager_client: AsyncClient,
        team_with_members: Team,
        manager_user: User,
        another_user: User,
    ) -> None:
        """Cannot add participant not in team."""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)

        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Meeting",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [another_user.id],
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_meeting_time_conflict(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Cannot create meeting with time conflict."""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)

        meeting1 = Meeting(
            title="Existing Meeting",
            start_time=start_time,
            end_time=end_time,
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user, regular_user],
        )
        test_session.add(meeting1)
        await test_session.commit()

        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Conflicting Meeting",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [regular_user.id],
            },
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_meeting_partial_overlap(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Cannot create meeting with partial time overlap."""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=2)

        meeting1 = Meeting(
            title="Existing Meeting",
            start_time=start_time,
            end_time=end_time,
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )
        test_session.add(meeting1)
        await test_session.commit()

        new_start = start_time + timedelta(hours=1)
        new_end = new_start + timedelta(hours=2)

        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Overlapping Meeting",
                "start_time": new_start.isoformat(),
                "end_time": new_end.isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [],
            },
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_meeting_nonexistent_team(
        self,
        manager_client: AsyncClient,
        manager_user: User,
    ) -> None:
        """Cannot create meeting for nonexistent team."""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)

        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Meeting",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "team_id": 99999,
                "participant_ids": [],
            },
        )

        assert response.status_code == 404


class TestGetMeeting:
    """Tests for GET /meetings/{meeting_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_meeting_as_participant(
        self,
        regular_client: AsyncClient,
        meeting: Meeting,
        regular_user: User,
    ) -> None:
        """Participant can view meeting."""
        response = await regular_client.get(
            f"/v1/meetings/{meeting.id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meeting.id
        assert data["title"] == meeting.title

    @pytest.mark.asyncio
    async def test_get_meeting_as_organizer(
        self,
        manager_client: AsyncClient,
        meeting: Meeting,
        manager_user: User,
    ) -> None:
        """Organizer can view meeting."""
        response = await manager_client.get(
            f"/v1/meetings/{meeting.id}",
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_meeting_unauthorized(
        self,
        another_client: AsyncClient,
        meeting: Meeting,
        another_user: User,
    ) -> None:
        """Non-participant cannot view meeting."""
        response = await another_client.get(
            f"/v1/meetings/{meeting.id}",
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_nonexistent_meeting(
        self,
        regular_client: AsyncClient,
        regular_user: User,
    ) -> None:
        """Cannot get nonexistent meeting."""
        response = await regular_client.get(
            "/v1/meetings/99999",
        )

        assert response.status_code == 404


class TestGetUserMeetings:
    """Tests for GET /meetings endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_meetings(
        self,
        regular_client: AsyncClient,
        meeting: Meeting,
        regular_user: User,
    ) -> None:
        """User can see their meetings."""
        response = await regular_client.get(
            "/v1/meetings/",
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(m["id"] == meeting.id for m in data)

    @pytest.mark.asyncio
    async def test_get_user_meetings_with_date_filter(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Can filter meetings by date range."""
        now = datetime.now()

        past_meeting = Meeting(
            title="Past Meeting",
            start_time=now - timedelta(days=7),
            end_time=now - timedelta(days=7, hours=-1),
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )

        future_meeting = Meeting(
            title="Future Meeting",
            start_time=now + timedelta(days=7),
            end_time=now + timedelta(days=7, hours=1),
            team_id=team_with_members.id,
            organizer_id=manager_user.id,
            participants=[manager_user],
        )

        test_session.add_all([past_meeting, future_meeting])
        await test_session.commit()

        response = await manager_client.get(
            "/v1/meetings/",
            params={
                "start_date": now.isoformat(),
                "end_date": (now + timedelta(days=30)).isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        meeting_ids = [m["id"] for m in data]

        assert future_meeting.id in meeting_ids
        assert past_meeting.id not in meeting_ids

    @pytest.mark.asyncio
    async def test_get_user_meetings_empty(
        self,
        another_client: AsyncClient,
        another_user: User,
    ) -> None:
        """User with no meetings sees empty list."""
        response = await another_client.get(
            "/v1/meetings/",
        )

        assert response.status_code == 200
        assert response.json() == []


class TestCancelMeeting:
    """Tests for DELETE /meetings/{meeting_id} endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_meeting_as_organizer(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        meeting: Meeting,
        manager_user: User,
    ) -> None:
        """Organizer can cancel meeting."""
        meeting_id = meeting.id

        response = await manager_client.delete(
            f"/v1/meetings/{meeting_id}",
        )

        assert response.status_code == 204

        result = await test_session.get(Meeting, meeting_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_meeting_as_participant(
        self,
        regular_client: AsyncClient,
        meeting: Meeting,
        regular_user: User,
    ) -> None:
        """Participant cannot cancel meeting."""
        response = await regular_client.delete(
            f"/v1/meetings/{meeting.id}",
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_meeting_unauthorized(
        self,
        another_client: AsyncClient,
        meeting: Meeting,
        another_user: User,
    ) -> None:
        """Non-participant cannot cancel meeting."""
        response = await another_client.delete(
            f"/v1/meetings/{meeting.id}",
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_meeting(
        self,
        manager_client: AsyncClient,
        manager_user: User,
    ) -> None:
        """Cannot cancel nonexistent meeting."""
        response = await manager_client.delete(
            "/v1/meetings/99999",
        )

        assert response.status_code == 404
