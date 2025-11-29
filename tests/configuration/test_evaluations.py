from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Evaluation, Task, Team, User
from app.models.task import TaskStatus


class TestEvaluations:
    """Tests for evaluation endpoints."""

    URL_EVALUATIONS = f"v1{settings.api.v1.tasks}/{{task_id}}{settings.api.v1.evaluations}"

    @pytest.mark.asyncio
    async def test_create_evaluation_as_manager(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        completed_task: Task,
        manager_user: User,
    ) -> None:
        """Manager can evaluate completed task."""
        response = await manager_client.post(
            self.URL_EVALUATIONS.format(task_id=completed_task.id),
            json={"rating": 5},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["task_id"] == completed_task.id

    @pytest.mark.asyncio
    async def test_create_evaluation_as_admin(
        self,
        admin_client: AsyncClient,
        completed_task: Task,
        admin_user: User,
    ) -> None:
        """Admin can evaluate any completed task."""
        response = await admin_client.post(
            self.URL_EVALUATIONS.format(task_id=completed_task.id),
            json={"rating": 4},
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_evaluation_not_completed(
        self,
        manager_client: AsyncClient,
        task: Task,
        manager_user: User,
    ) -> None:
        """Cannot evaluate task that is not completed."""
        response = await manager_client.post(
            f"/v1/tasks/{task.id}/evaluations",
            json={"rating": 5},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_evaluation_already_exists(
        self,
        manager_client: AsyncClient,
        completed_task: Task,
        evaluation: Evaluation,
        manager_user: User,
    ) -> None:
        """Cannot create duplicate evaluation."""
        response = await manager_client.post(
            self.URL_EVALUATIONS.format(task_id=completed_task.id),
            json={"rating": 3},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_evaluation_invalid_rating(
        self,
        manager_client: AsyncClient,
        completed_task: Task,
        manager_user: User,
    ) -> None:
        """Cannot create evaluation with invalid rating."""
        # Rating too low
        response = await manager_client.post(
            self.URL_EVALUATIONS.format(task_id=completed_task.id),
            json={"rating": 0},
        )
        assert response.status_code == 422

        # Rating too high
        response = await manager_client.post(
            self.URL_EVALUATIONS.format(task_id=completed_task.id),
            json={"rating": 6},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_evaluation_manager_wrong_team(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        manager_user: User,
    ) -> None:
        """Manager cannot evaluate task from team they don't belong to."""
        # Create team and task without manager
        other_team = Team(name="Other Team", invite_code="OTHER123")
        test_session.add(other_team)
        await test_session.flush()

        other_task = Task(
            title="Other Task",
            status=TaskStatus.COMPLETED,
            team_id=other_team.id,
        )
        test_session.add(other_task)
        await test_session.commit()

        response = await manager_client.post(
            self.URL_EVALUATIONS.format(task_id=other_task.id),
            json={"rating": 5},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_my_evaluations(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        regular_user: User,
        manager_user: User,
    ) -> None:
        """User can get their own evaluations."""
        # Create completed tasks with evaluations
        task1 = Task(
            title="Task 1",
            status=TaskStatus.COMPLETED,
            team_id=team_with_members.id,
            assignee_id=regular_user.id,
        )
        task2 = Task(
            title="Task 2",
            status=TaskStatus.COMPLETED,
            team_id=team_with_members.id,
            assignee_id=regular_user.id,
        )
        test_session.add_all([task1, task2])
        await test_session.flush()

        eval1 = Evaluation(rating=5, task_id=task1.id)
        eval2 = Evaluation(rating=4, task_id=task2.id)
        test_session.add_all([eval1, eval2])
        await test_session.commit()

        response = await regular_client.get(
            "/v1/tasks/evaluations/me",
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        ratings = [e["rating"] for e in data]
        assert 5 in ratings
        assert 4 in ratings

    @pytest.mark.asyncio
    async def test_get_average_rating_own(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        regular_user: User,
    ) -> None:
        """User can get their own average rating."""
        now = datetime.now()
        start = now - timedelta(days=30)
        end = now

        # Create evaluated tasks
        task1 = Task(
            title="Task 1",
            status=TaskStatus.COMPLETED,
            team_id=team_with_members.id,
            assignee_id=regular_user.id,
        )
        task2 = Task(
            title="Task 2",
            status=TaskStatus.COMPLETED,
            team_id=team_with_members.id,
            assignee_id=regular_user.id,
        )
        test_session.add_all([task1, task2])
        await test_session.flush()

        eval1 = Evaluation(rating=4, task_id=task1.id)
        eval2 = Evaluation(rating=5, task_id=task2.id)
        test_session.add_all([eval1, eval2])
        await test_session.commit()

        response = await regular_client.get(
            f"/v1/tasks/evaluations/average/{regular_user.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["average_rating"] == 4.5

    @pytest.mark.asyncio
    async def test_get_average_rating_as_manager(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        regular_user: User,
        manager_user: User,
    ) -> None:
        """Manager can get any user's average rating."""
        now = datetime.now()

        response = await manager_client.get(
            f"/v1/tasks/evaluations/average/{regular_user.id}",
            params={
                "start_date": (now - timedelta(days=30)).isoformat(),
                "end_date": now.isoformat(),
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_average_rating_unauthorized(
        self,
        regular_client: AsyncClient,
        regular_user: User,
        another_user: User,
    ) -> None:
        """Regular user cannot get other user's average rating."""
        now = datetime.now()

        response = await regular_client.get(
            f"/v1/tasks/evaluations/average/{another_user.id}",
            params={
                "start_date": (now - timedelta(days=30)).isoformat(),
                "end_date": now.isoformat(),
            },
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_average_rating_no_evaluations(
        self,
        regular_client: AsyncClient,
        regular_user: User,
    ) -> None:
        """Returns None for user with no evaluations."""
        now = datetime.now()

        response = await regular_client.get(
            f"/v1/tasks/evaluations/average/{regular_user.id}",
            params={
                "start_date": (now - timedelta(days=30)).isoformat(),
                "end_date": now.isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["average_rating"] is None
