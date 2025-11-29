import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Team, User


class TestCreateTeam:
    """Tests for POST /teams endpoint."""

    @pytest.mark.asyncio
    async def test_create_team_as_admin(
        self,
        admin_client: AsyncClient,
        admin_user: User,
    ) -> None:
        """Admin can create a team."""
        response = await admin_client.post(
            "/v1/teams",
            json={"name": "New Team"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Team"
        assert "invite_code" in data
        assert len(data["invite_code"]) > 0

    @pytest.mark.asyncio
    async def test_create_team_as_manager(
        self,
        manager_client: AsyncClient,
        manager_user: User,
    ) -> None:
        """Manager cannot create a team."""
        response = await manager_client.post(
            "/v1/teams",
            json={"name": "New Team"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_team_duplicate_name(
        self,
        admin_client: AsyncClient,
        admin_user: User,
        team: Team,
    ) -> None:
        """Cannot create team with duplicate name."""
        response = await admin_client.post(
            "/v1/teams",
            json={"name": team.name},
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_team_empty_name(
        self,
        admin_client: AsyncClient,
        admin_user: User,
    ) -> None:
        """Cannot create team with empty name."""
        response = await admin_client.post(
            "/v1/teams",
            json={"name": "   "},
        )

        assert response.status_code == 422


class TestJoinTeam:
    """Tests for POST /teams/join endpoint."""

    @pytest.mark.asyncio
    async def test_join_team_success(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        regular_user: User,
        team: Team,
    ) -> None:
        """User can join team with valid invite code."""
        response = await regular_client.post(
            "/v1/teams/join",
            json={"invite_code": team.invite_code},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == team.id

        # Verify user was added to team
        await test_session.refresh(regular_user, attribute_names=["teams"])
        assert team in regular_user.teams

    @pytest.mark.asyncio
    async def test_join_team_invalid_code(
        self,
        regular_client: AsyncClient,
        regular_user: User,
    ) -> None:
        """Cannot join team with invalid invite code."""
        response = await regular_client.post(
            "/v1/teams/join",
            json={"invite_code": "INVALID"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_join_team_already_in_team(
        self,
        regular_client: AsyncClient,
        team_with_members: Team,
        regular_user: User,
    ) -> None:
        """Cannot join team if already in a team."""
        response = await regular_client.post(
            "/v1/teams/join",
            json={"invite_code": team_with_members.invite_code},
        )

        assert response.status_code == 400


class TestLeaveTeam:
    """Tests for DELETE /teams/{team_id}/leave endpoint."""

    @pytest.mark.asyncio
    async def test_leave_team_success(
        self,
        regular_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        regular_user: User,
    ) -> None:
        """User can leave their team."""
        response = await regular_client.delete(
            f"/v1/teams/{team_with_members.id}/leave",
        )

        assert response.status_code == 204

        # Verify user was removed
        await test_session.refresh(regular_user, attribute_names=["teams"])
        assert team_with_members not in regular_user.teams

    @pytest.mark.asyncio
    async def test_leave_team_not_member(
        self,
        regular_client: AsyncClient,
        team: Team,
        regular_user: User,
    ) -> None:
        """Cannot leave team if not a member."""
        response = await regular_client.delete(
            f"/v1/teams/{team.id}/leave",
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_leave_nonexistent_team(
        self,
        regular_client: AsyncClient,
        regular_user: User,
    ) -> None:
        """Cannot leave nonexistent team."""
        response = await regular_client.delete(
            "/v1/teams/99999/leave",
        )

        assert response.status_code == 400


class TestGetTeamMembers:
    """Tests for GET /teams/{team_id}/members endpoint."""

    @pytest.mark.asyncio
    async def test_get_members_as_admin(
        self,
        admin_client: AsyncClient,
        team_with_members: Team,
        admin_user: User,
    ) -> None:
        """Admin can view team members."""
        response = await admin_client.get(
            f"/v1/teams/{team_with_members.id}/members",
        )

        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert len(data["members"]) == 2

    @pytest.mark.asyncio
    async def test_get_members_as_manager(
        self,
        manager_client: AsyncClient,
        team_with_members: Team,
        manager_user: User,
    ) -> None:
        """Manager can view team members."""
        response = await manager_client.get(
            f"/v1/teams/{team_with_members.id}/members",
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_members_as_user(
        self,
        another_client: AsyncClient,
        team_with_members: Team,
        another_user: User,
    ) -> None:
        """Regular user cannot view team members."""
        response = await another_client.get(
            f"/v1/teams/{team_with_members.id}/members",
        )

        assert response.status_code == 403


class TestAddTeamMember:
    """Tests for POST /teams/{team_id}/members/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_add_member_as_admin(
        self,
        admin_client: AsyncClient,
        test_session: AsyncSession,
        team: Team,
        admin_user: User,
        regular_user: User,
    ) -> None:
        """Admin can add user to any team."""
        response = await admin_client.post(
            f"/v1/teams/{team.id}/members/{regular_user.id}",
        )

        assert response.status_code == 200

        await test_session.refresh(team, attribute_names=["members"])
        assert regular_user in team.members

    @pytest.mark.asyncio
    async def test_add_member_as_manager_own_team(
        self,
        manager_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        manager_user: User,
        another_user: User,
    ) -> None:
        """Manager can add user to their own team."""
        response = await manager_client.post(
            f"/v1/teams/{team_with_members.id}/members/{another_user.id}",
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_member_as_manager_other_team(
        self,
        manager_client: AsyncClient,
        team: Team,
        manager_user: User,
        regular_user: User,
    ) -> None:
        """Manager cannot add user to other team."""
        response = await manager_client.post(
            f"/v1/teams/{team.id}/members/{regular_user.id}",
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_member_already_in_team(
        self,
        admin_client: AsyncClient,
        team_with_members: Team,
        regular_user: User,
    ) -> None:
        """Cannot add user who is already in team."""
        response = await admin_client.post(
            f"/v1/teams/{team_with_members.id}/members/{regular_user.id}",
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_nonexistent_user(
        self,
        admin_client: AsyncClient,
        team: Team,
    ) -> None:
        """Cannot add nonexistent user."""
        response = await admin_client.post(
            f"/v1/teams/{team.id}/members/99999",
        )

        assert response.status_code == 404


class TestRemoveTeamMember:
    """Tests for DELETE /teams/{team_id}/members/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_remove_member_as_admin(
        self,
        admin_client: AsyncClient,
        test_session: AsyncSession,
        team_with_members: Team,
        regular_user: User,
    ) -> None:
        """Admin can remove user from any team."""
        response = await admin_client.delete(
            f"/v1/teams/{team_with_members.id}/members/{regular_user.id}",
        )

        assert response.status_code == 200

        await test_session.refresh(team_with_members, attribute_names=["members"])
        assert regular_user not in team_with_members.members

    @pytest.mark.asyncio
    async def test_remove_member_as_manager_own_team(
        self,
        manager_client: AsyncClient,
        team_with_members: Team,
        regular_user: User,
    ) -> None:
        """Manager can remove user from their own team."""
        response = await manager_client.delete(
            f"/v1/teams/{team_with_members.id}/members/{regular_user.id}",
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_remove_member_not_in_team(
        self,
        admin_client: AsyncClient,
        team: Team,
        regular_user: User,
    ) -> None:
        """Cannot remove user who is not in team."""
        response = await admin_client.delete(
            f"/v1/teams/{team.id}/members/{regular_user.id}",
        )

        assert response.status_code == 400
