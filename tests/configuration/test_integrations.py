from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Team, User
from app.models.task import TaskStatus


@pytest.mark.integration
class TestTeamWorkflow:
    """Test complete team creation and management workflow."""

    @pytest.mark.asyncio
    async def test_complete_team_workflow(
        self,
        admin_client: AsyncClient,
        regular_client: AsyncClient,
        another_client: AsyncClient,
        test_session: AsyncSession,
        admin_user: User,
        regular_user: User,
        another_user: User,
    ) -> None:
        """Test: Create team -> Add members -> Create task -> Complete workflow."""
        # 1. Admin creates team
        response = await admin_client.post(
            "/v1/teams",
            json={"name": "Project Alpha"},
        )
        assert response.status_code == 201
        team_data = response.json()
        team_id = team_data["id"]
        invite_code = team_data["invite_code"]

        # 2. User joins team with invite code
        response = await regular_client.post(
            "/v1/teams/join",
            json={"invite_code": invite_code},
        )
        assert response.status_code == 200

        # 3. Admin adds another member directly
        response = await admin_client.post(
            f"/v1/teams/{team_id}/members/{another_user.id}",
        )
        assert response.status_code == 200

        # 4. Verify team has 2 members
        response = await admin_client.get(
            f"/v1/teams/{team_id}/members",
        )
        assert response.status_code == 200
        members = response.json()["members"]
        assert len(members) == 2


@pytest.mark.integration
class TestTaskLifecycle:
    """Test complete task lifecycle."""

    @pytest.mark.asyncio
    async def test_task_creation_to_evaluation(
        self,
        manager_client: AsyncClient,
        regular_client: AsyncClient,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Test: Create task -> Assign -> Update -> Complete -> Evaluate."""
        # 1. Manager creates task
        deadline = datetime.now() + timedelta(days=7)
        response = await manager_client.post(
            "/v1/tasks/",
            json={
                "title": "Implement Feature X",
                "description": "Build the new feature",
                "team_id": team_with_members.id,
                "assignee_id": regular_user.id,
                "deadline": deadline.isoformat(),
            },
        )
        assert response.status_code == 201
        task = response.json()
        task_id = task["id"]
        assert task["status"] == TaskStatus.OPEN.value

        # 2. Assignee updates task to in progress
        response = await regular_client.patch(
            f"/v1/tasks/{task_id}",
            json={"status": TaskStatus.IN_PROGRESS.value},
        )
        assert response.status_code == 200
        assert response.json()["status"] == TaskStatus.IN_PROGRESS.value

        # 3. Assignee adds a comment
        response = await regular_client.post(
            f"/v1/tasks/{task_id}/comments/",
            params={"task_id": task_id},
            json={"content": "Working on this now"},
        )
        assert response.status_code == 201

        # 4. Assignee completes task
        response = await regular_client.patch(
            f"/v1/tasks/{task_id}",
            json={"status": TaskStatus.COMPLETED.value},
        )
        assert response.status_code == 200

        # 5. Manager evaluates completed task
        response = await manager_client.post(
            f"/v1/tasks/{task_id}/evaluations",
            json={"rating": 5},
        )
        assert response.status_code == 201
        assert response.json()["rating"] == 5

        # 6. Verify evaluation appears in user's evaluations
        response = await regular_client.get(
            "/v1/tasks/evaluations/me",
        )
        assert response.status_code == 200
        evaluations = response.json()
        assert any(e["task_id"] == task_id for e in evaluations)


@pytest.mark.integration
class TestMeetingScheduling:
    """Test meeting scheduling workflow."""

    @pytest.mark.asyncio
    async def test_schedule_multiple_meetings(
        self,
        manager_client: AsyncClient,
        regular_client: AsyncClient,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Test scheduling multiple non-conflicting meetings."""
        base_time = datetime.now() + timedelta(hours=2)

        # 1. Schedule first meeting
        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Sprint Planning",
                "start_time": base_time.isoformat(),
                "end_time": (base_time + timedelta(hours=1)).isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [regular_user.id],
            },
        )
        assert response.status_code == 201
        meeting1_id = response.json()["id"]

        # 2. Schedule second meeting (non-conflicting)
        second_time = base_time + timedelta(hours=2)
        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Daily Standup",
                "start_time": second_time.isoformat(),
                "end_time": (second_time + timedelta(minutes=15)).isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [regular_user.id],
            },
        )
        assert response.status_code == 201
        meeting2_id = response.json()["id"]

        # 3. Try conflicting meeting
        conflict_time = base_time + timedelta(minutes=30)
        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Conflicting Meeting",
                "start_time": conflict_time.isoformat(),
                "end_time": (conflict_time + timedelta(hours=1)).isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [regular_user.id],
            },
        )
        assert response.status_code == 409

        # 4. Get user's meetings
        response = await regular_client.get(
            "/v1/meetings/",
        )
        assert response.status_code == 200
        meetings = response.json()
        meeting_ids = [m["id"] for m in meetings]
        assert meeting1_id in meeting_ids
        assert meeting2_id in meeting_ids


@pytest.mark.integration
class TestCalendarIntegration:
    """Test calendar view with mixed events."""

    @pytest.mark.asyncio
    async def test_calendar_view_with_tasks_and_meetings(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Test calendar shows both tasks and meetings."""
        target_date = datetime.now().date() + timedelta(days=1)
        target_datetime = datetime.combine(target_date, datetime.min.time())

        # 1. Create a task
        response = await manager_client.post(
            "/v1/tasks/",
            json={
                "title": "Review Code",
                "team_id": team_with_members.id,
                "deadline": (target_datetime + timedelta(hours=10)).isoformat(),
            },
        )
        assert response.status_code == 201
        task_id = response.json()["id"]

        # 2. Create a meeting
        response = await manager_client.post(
            "/v1/meetings/",
            json={
                "title": "Code Review Meeting",
                "start_time": (target_datetime + timedelta(hours=14)).isoformat(),
                "end_time": (target_datetime + timedelta(hours=15)).isoformat(),
                "team_id": team_with_members.id,
                "participant_ids": [],
            },
        )
        assert response.status_code == 201
        meeting_id = response.json()["id"]

        # 3. Get calendar
        response = await manager_client.post(
            "/v1/calendar/events",
            json={"day": target_date.isoformat()},
        )
        assert response.status_code == 200

        data = response.json()
        events = data["events"]

        # 4. Verify events
        event_ids = [(e["type"], e["id"]) for e in events]
        assert ("task", task_id) in event_ids
        assert ("meeting", meeting_id) in event_ids

        # 5. Verify ordering
        task_event = next(e for e in events if e["type"] == "task" and e["id"] == task_id)
        meeting_event = next(e for e in events if e["type"] == "meeting" and e["id"] == meeting_id)

        task_index = events.index(task_event)
        meeting_index = events.index(meeting_event)
        assert task_index < meeting_index


@pytest.mark.integration
class TestPermissionWorkflows:
    """Test permission workflows across different roles."""

    @pytest.mark.asyncio
    async def test_manager_team_management(
        self,
        admin_client: AsyncClient,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        admin_user: User,
        manager_user: User,
        regular_user: User,
        another_user: User,
    ) -> None:
        """Test manager can only manage their own team."""
        # 1. Admin creates two teams
        response = await admin_client.post("/v1/teams", json={"name": "Team A"})
        team_a_id = response.json()["id"]

        response = await admin_client.post("/v1/teams", json={"name": "Team B"})
        team_b_id = response.json()["id"]

        # 2. Add manager to Team A only
        response = await admin_client.post(
            f"/v1/teams/{team_a_id}/members/{manager_user.id}",
        )
        assert response.status_code == 200

        # 3. Manager can add user to Team A
        response = await manager_client.post(
            f"/v1/teams/{team_a_id}/members/{regular_user.id}",
        )
        assert response.status_code == 200

        # 4. Manager cannot add user to Team B
        response = await manager_client.post(
            f"/v1/teams/{team_b_id}/members/{another_user.id}",
        )
        assert response.status_code == 403

        # 5. Manager can create task in Team A
        response = await manager_client.post(
            "/v1/tasks/",
            json={"title": "Task in Team A", "team_id": team_a_id},
        )
        assert response.status_code == 201

        # 6. Manager cannot create task in Team B
        response = await manager_client.post(
            "/v1/tasks/",
            json={"title": "Task in Team B", "team_id": team_b_id},
        )
        assert response.status_code == 403


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across operations."""

    @pytest.mark.asyncio
    async def test_task_cascade_deletes(
        self,
        manager_client: AsyncClient,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Test that deleting task cascades to comments and evaluations."""
        # 1. Create and complete task
        response = await manager_client.post(
            "/v1/tasks/",
            json={
                "title": "Task to Delete",
                "team_id": team_with_members.id,
                "assignee_id": regular_user.id,
            },
        )
        task_id = response.json()["id"]

        # 2. Add comment
        response = await regular_client.post(
            f"/v1/tasks/{task_id}/comments/",
            params={"task_id": task_id},
            json={"content": "Test comment"},
        )
        comment_id = response.json()["id"]

        # 3. Complete and evaluate
        await regular_client.patch(
            f"/v1/tasks/{task_id}",
            json={"status": TaskStatus.COMPLETED.value},
        )

        response = await manager_client.post(
            f"/v1/tasks/{task_id}/evaluations",
            json={"rating": 4},
        )
        assert response.status_code == 201

        # 4. Delete task
        response = await manager_client.delete(
            f"/v1/tasks/{task_id}",
        )
        assert response.status_code == 204

        # 5. Verify comment deleted
        response = await regular_client.get(
            f"/v1/tasks/{task_id}/comments/",
            params={"task_id": task_id},
        )
        comments = response.json()
        assert not any(c["id"] == comment_id for c in comments)

        # 6. Verify evaluation deleted
        response = await regular_client.get(
            "/v1/tasks/evaluations/me",
        )
        evaluations = response.json()
        assert not any(e["task_id"] == task_id for e in evaluations)

    @pytest.mark.asyncio
    async def test_team_member_removal_consistency(
        self,
        admin_client: AsyncClient,
        regular_client: AsyncClient,
        team_with_members: Team,
        admin_user: User,
        regular_user: User,
    ) -> None:
        """Test removing team member doesn't break existing data."""
        # 1. Create task
        response = await admin_client.post(
            "/v1/tasks/",
            json={
                "title": "User's Task",
                "team_id": team_with_members.id,
                "assignee_id": regular_user.id,
            },
        )
        task_id = response.json()["id"]
        # 2. Remove user
        response = await admin_client.delete(
            f"/v1/teams/{team_with_members.id}/members/{regular_user.id}",
        )
        assert response.status_code == 200

        # 3. Task still exists
        response = await admin_client.get(
            "/v1/tasks/",
        )
        tasks = response.json()

        task = next((t for t in tasks if t["id"] == task_id), None)
        assert task is not None
        assert task["assignee_id"] == regular_user.id

        # 4. Removed user cannot access task
        response = await regular_client.patch(
            f"/v1/tasks/{task_id}",
            json={"status": TaskStatus.IN_PROGRESS.value},
        )
        assert response.status_code == 403
