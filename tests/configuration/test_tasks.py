from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, Team, User
from app.models.task import TaskStatus
from tests.helpers import unique_string


class TestCreateTask:
    """Tests for POST /tasks endpoint."""

    @pytest.mark.asyncio
    async def test_create_task_as_manager(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Manager can create task in their team."""
        deadline = datetime.now() + timedelta(days=7)

        response = await manager_client.post(
            "/v1/tasks/",
            json={
                "title": "New Task",
                "description": "Task description",
                "team_id": team_with_members.id,
                "assignee_id": regular_user.id,
                "deadline": deadline.isoformat(),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["team_id"] == team_with_members.id
        assert data["assignee_id"] == regular_user.id
        assert data["creator_id"] == manager_user.id

    @pytest.mark.asyncio
    async def test_create_task_as_admin_any_team(
        self,
        admin_client: AsyncClient,
        team_with_members: Team,
        admin_user: User,
        regular_user: User,
    ) -> None:
        """Admin can create task in any team."""
        response = await admin_client.post(
            "/v1/tasks/",
            json={
                "title": "Admin Task",
                "description": "Description",
                "team_id": team_with_members.id,
                "assignee_id": regular_user.id,
            },
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_task_manager_wrong_team(
        self,
        manager_client: AsyncClient,
        team: Team,
        manager_user: User,
    ) -> None:
        """Manager cannot create task in team they don't belong to."""
        response = await manager_client.post(
            "/v1/tasks/",
            json={
                "title": "Task",
                "team_id": team.id,
            },
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_task_invalid_assignee(
        self,
        manager_client: AsyncClient,
        team_with_members: Team,
        manager_user: User,
        another_user: User,
    ) -> None:
        """Cannot assign task to user not in team."""
        response = await manager_client.post(
            "/v1/tasks/",
            json={
                "title": "Task",
                "team_id": team_with_members.id,
                "assignee_id": another_user.id,
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_task_nonexistent_team(
        self,
        admin_client: AsyncClient,
        admin_user: User,
    ) -> None:
        """Cannot create task for nonexistent team."""
        response = await admin_client.post(
            "/v1/tasks/",
            json={
                "title": "Task",
                "team_id": 99999,
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_task_as_regular_user(
        self,
        regular_client: AsyncClient,
        team_with_members: Team,
        regular_user: User,
    ) -> None:
        """Regular user cannot create tasks."""
        response = await regular_client.post(
            "/v1/tasks/",
            json={
                "title": "Task",
                "team_id": team_with_members.id,
            },
        )

        assert response.status_code == 403


class TestUpdateTask:
    """Tests for PATCH /tasks/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_task_as_assignee(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        task: Task,
        regular_user: User,
    ) -> None:
        """Assignee can update their task."""
        response = await regular_client.patch(
            f"/v1/tasks/{task.id}",
            json={
                "status": TaskStatus.IN_PROGRESS.value,
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == TaskStatus.IN_PROGRESS.value
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_task_as_manager(
        self,
        manager_client: AsyncClient,
        task: Task,
        manager_user: User,
    ) -> None:
        """Manager can update task in their team."""
        response = await manager_client.patch(
            f"/v1/tasks/{task.id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_task_as_admin(
        self,
        admin_client: AsyncClient,
        task: Task,
        admin_user: User,
    ) -> None:
        """Admin can update any task."""
        response = await admin_client.patch(
            f"/v1/tasks/{task.id}",
            json={"status": TaskStatus.COMPLETED.value},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_task_unauthorized_user(
        self,
        another_client: AsyncClient,
        task: Task,
        another_user: User,
    ) -> None:
        """User not in team cannot update task."""
        response = await another_client.patch(
            f"/v1/tasks/{task.id}",
            json={"title": "Hacked"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_task_change_assignee(
        self,
        manager_client: AsyncClient,
        task: Task,
        manager_user: User,
    ) -> None:
        """Can change task assignee to another team member."""
        response = await manager_client.patch(
            f"/v1/tasks/{task.id}",
            json={"assignee_id": manager_user.id},
        )

        assert response.status_code == 200
        assert response.json()["assignee_id"] == manager_user.id

    @pytest.mark.asyncio
    async def test_update_task_invalid_assignee(
        self,
        manager_client: AsyncClient,
        task: Task,
        manager_user: User,
        another_user: User,
    ) -> None:
        """Cannot change assignee to user not in team."""
        response = await manager_client.patch(
            f"/v1/tasks/{task.id}",
            json={"assignee_id": another_user.id},
        )

        assert response.status_code == 400


class TestDeleteTask:
    """Tests for DELETE /tasks/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_task_as_manager(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        task: Task,
        manager_user: User,
    ) -> None:
        """Manager can delete task in their team."""
        task_id = task.id

        response = await manager_client.delete(
            f"/v1/tasks/{task_id}",
        )

        assert response.status_code == 204

        result = await test_session.get(Task, task_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_task_as_admin(
        self,
        admin_client: AsyncClient,
        task: Task,
        admin_user: User,
    ) -> None:
        """Admin can delete any task."""
        response = await admin_client.delete(
            f"/v1/tasks/{task.id}",
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_task_as_regular_user(
        self,
        regular_client: AsyncClient,
        task: Task,
        regular_user: User,
    ) -> None:
        """Regular user cannot delete tasks."""
        response = await regular_client.delete(
            f"/v1/tasks/{task.id}",
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(
        self,
        manager_client: AsyncClient,
        manager_user: User,
    ) -> None:
        """Cannot delete nonexistent task."""
        response = await manager_client.delete(
            "/v1/tasks/99999",
        )

        assert response.status_code == 404


class TestListTasks:
    """Tests for GET /tasks endpoint."""

    @pytest.mark.asyncio
    async def test_list_tasks_as_admin(
        self,
        admin_client: AsyncClient,
        task: Task,
        admin_user: User,
    ) -> None:
        """Admin sees all tasks."""
        response = await admin_client.get("/v1/tasks/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(t["id"] == task.id for t in data)

    @pytest.mark.asyncio
    async def test_list_tasks_as_manager(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Manager sees only tasks from their teams."""
        task1 = Task(
            title="Team Task",
            team_id=team_with_members.id,
            creator_id=manager_user.id,
        )
        test_session.add(task1)

        other_team = Team(name=unique_string("TestTeam", length=6), invite_code=unique_string("CODE", length=8))
        test_session.add(other_team)
        await test_session.flush()

        task2 = Task(
            title="Other Task",
            team_id=other_team.id,
            creator_id=manager_user.id,
        )
        test_session.add(task2)
        await test_session.commit()

        response = await manager_client.get("/v1/tasks/")

        assert response.status_code == 200
        data = response.json()
        task_ids = [t["id"] for t in data]

        assert task1.id in task_ids
        assert task2.id not in task_ids

    @pytest.mark.asyncio
    async def test_list_tasks_as_regular_user(
        self,
        regular_client: AsyncClient,
        task: Task,
        regular_user: User,
    ) -> None:
        """Regular user sees only tasks from their teams."""
        response = await regular_client.get("/v1/tasks/")

        assert response.status_code == 200
        data = response.json()
        assert any(t["id"] == task.id for t in data)

    @pytest.mark.asyncio
    async def test_list_tasks_empty(
        self,
        another_client: AsyncClient,
        another_user: User,
    ) -> None:
        """User with no teams sees no tasks."""
        response = await another_client.get("/v1/tasks/")

        assert response.status_code == 200
        assert response.json() == []


class TestTaskPermissions:
    """Tests for task access control logic."""

    @pytest.mark.asyncio
    async def test_task_cascade_delete_with_comments(
        self,
        test_session: AsyncSession,
        task: Task,
        comment,
    ) -> None:
        """Deleting task deletes associated comments."""
        from app.models import Comment

        comment_id = comment.id

        await test_session.delete(task)
        await test_session.commit()

        result = await test_session.get(Comment, comment_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_task_with_null_creator(
        self,
        test_session: AsyncSession,
        team: Team,
    ) -> None:
        """Task can exist with null creator (if user deleted)."""
        task = Task(
            title="Orphan Task",
            team_id=team.id,
            creator_id=None,
            assignee_id=None,
        )
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)

        assert task.creator_id is None
        assert task.id is not None
