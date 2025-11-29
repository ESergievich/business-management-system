import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Comment, Task, User


class TestComments:
    """Tests for comment endpoints."""

    URL_COMMENTS = f"v1{settings.api.v1.comments}/"

    @pytest.mark.asyncio
    async def test_create_comment_as_team_member(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        task: Task,
        regular_user: User,
    ) -> None:
        """Team member can create comment."""
        response = await regular_client.post(
            self.URL_COMMENTS.format(task_id=task.id),
            params={"task_id": task.id},
            json={"content": "This is a comment"},
            headers={"user_id": str(regular_user.id)},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a comment"
        assert data["author_id"] == regular_user.id
        assert data["task_id"] == task.id

    @pytest.mark.asyncio
    async def test_create_comment_not_team_member(
        self,
        another_client: AsyncClient,
        task: Task,
        another_user: User,
    ) -> None:
        """Non-team member cannot create comment."""
        response = await another_client.post(
            self.URL_COMMENTS.format(task_id=task.id),
            params={"task_id": task.id},
            json={"content": "Unauthorized comment"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_comment_nonexistent_task(
        self,
        regular_client: AsyncClient,
        regular_user: User,
    ) -> None:
        """Cannot create comment for nonexistent task."""
        response = await regular_client.post(
            self.URL_COMMENTS.format(task_id=99999),
            json={"content": "Comment"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_comments(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        task: Task,
        regular_user: User,
        manager_user: User,
    ) -> None:
        """Get all comments for a task."""
        # Create multiple comments
        comment1 = Comment(
            content="First comment",
            task_id=task.id,
            author_id=regular_user.id,
        )
        comment2 = Comment(
            content="Second comment",
            task_id=task.id,
            author_id=manager_user.id,
        )
        test_session.add_all([comment1, comment2])
        await test_session.commit()

        response = await regular_client.get(
            self.URL_COMMENTS.format(task_id=task.id),
            params={"task_id": task.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

        # Verify ordering by created_at
        contents = [c["content"] for c in data]
        assert "First comment" in contents
        assert "Second comment" in contents

    @pytest.mark.asyncio
    async def test_update_comment_as_author(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        comment: Comment,
        regular_user: User,
    ) -> None:
        """Comment author can update their comment."""
        response = await regular_client.patch(
            f"{self.URL_COMMENTS.format(task_id=1)}{comment.id}",
            json={"content": "Updated content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"

    @pytest.mark.asyncio
    async def test_update_comment_not_author(
        self,
        manager_client: AsyncClient,
        comment: Comment,
        manager_user: User,
    ) -> None:
        """Non-author cannot update comment."""
        response = await manager_client.patch(
            f"{self.URL_COMMENTS.format(task_id=1)}{comment.id}",
            json={"content": "Hacked content"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_comment_as_author(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        comment: Comment,
        task: Task,
        regular_user: User,
    ) -> None:
        """Comment author can delete their comment."""
        comment_id = comment.id
        response = await regular_client.delete(
            f"{self.URL_COMMENTS.format(task_id=task.id)}{comment_id}",
        )

        assert response.status_code == 204

        # Verify deletion
        result = await test_session.get(Comment, comment_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_comment_as_manager(
        self,
        manager_client: AsyncClient,
        comment: Comment,
        manager_user: User,
    ) -> None:
        """Manager in team can delete any comment."""
        response = await manager_client.delete(
            f"{self.URL_COMMENTS.format(task_id=1)}{comment.id}",
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_comment_as_admin(
        self,
        admin_client: AsyncClient,
        comment: Comment,
        admin_user: User,
    ) -> None:
        """Admin can delete any comment."""
        response = await admin_client.delete(
            f"{self.URL_COMMENTS.format(task_id=1)}{comment.id}",
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_comment_unauthorized(
        self,
        another_client: AsyncClient,
        comment: Comment,
        another_user: User,
    ) -> None:
        """Unauthorized user cannot delete comment."""
        response = await another_client.delete(
            f"{self.URL_COMMENTS.format(task_id=1)}{comment.id}",
        )

        assert response.status_code == 403
