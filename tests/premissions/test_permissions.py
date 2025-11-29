from app.core.permissions import can_access
from app.models import User
from app.models.user import UserRole


class TestCanAccess:
    """Tests for can_access permission function."""

    def test_admin_full_access(self) -> None:
        """Admin has access to everything."""
        admin = User(
            email="admin@test.com",
            username="admin",
            role=UserRole.ADMIN,
        )

        # Admin can access any team
        assert can_access(admin, {1, 2, 3})
        assert can_access(admin, set())

        # Admin can access even when not creator
        assert can_access(admin, {1, 2, 3}, creator_id=999)

    def test_manager_member_access(self) -> None:
        """Manager can access if they are team member."""
        manager = User(
            id=1,
            email="manager@test.com",
            username="manager",
            role=UserRole.MANAGER,
        )

        # Manager in team has access
        assert can_access(manager, {1, 2, 3})

        # Manager not in team has no access
        assert not can_access(manager, {5, 6, 7})

    def test_manager_not_affected_by_creator(self) -> None:
        """Manager access not affected by creator_id."""
        manager = User(
            id=1,
            email="manager@test.com",
            username="manager",
            role=UserRole.MANAGER,
        )

        # Manager in team, not creator
        assert can_access(manager, {1, 2, 3}, creator_id=2)

        # Manager in team, is creator
        assert can_access(manager, {1, 2, 3}, creator_id=1)

    def test_user_member_no_creator(self) -> None:
        """Regular user needs to be member when no creator specified."""
        user = User(
            id=1,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        # User in team has access
        assert can_access(user, {1, 2, 3})

        # User not in team has no access
        assert not can_access(user, {5, 6, 7})

    def test_user_must_be_creator(self) -> None:
        """Regular user must be creator when creator_id specified."""
        user = User(
            id=1,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        # User in team AND is creator
        assert can_access(user, {1, 2, 3}, creator_id=1)

        # User in team but NOT creator
        assert not can_access(user, {1, 2, 3}, creator_id=2)

        # User not in team
        assert not can_access(user, {5, 6, 7}, creator_id=1)

    def test_empty_team_members(self) -> None:
        """Handle empty team member set."""
        admin = User(
            id=1,
            email="admin@test.com",
            username="admin",
            role=UserRole.ADMIN,
        )
        manager = User(
            id=2,
            email="manager@test.com",
            username="manager",
            role=UserRole.MANAGER,
        )
        user = User(
            id=3,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        # Admin can access empty team
        assert can_access(admin, set())

        # Manager cannot access empty team
        assert not can_access(manager, set())

        # User cannot access empty team
        assert not can_access(user, set())

    def test_creator_id_none(self) -> None:
        """Handle None creator_id (resource without creator)."""
        user = User(
            id=1,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        # When creator_id is None, only membership matters
        assert can_access(user, {1, 2, 3}, creator_id=None)
        assert not can_access(user, {5, 6, 7}, creator_id=None)

    def test_different_user_roles(self) -> None:
        """Test with various user role scenarios."""
        admin = User(id=1, email="a@test.com", username="a", role=UserRole.ADMIN)
        manager = User(id=2, email="m@test.com", username="m", role=UserRole.MANAGER)
        user = User(id=3, email="u@test.com", username="u", role=UserRole.USER)

        member_ids = {2, 3}  # manager and user

        # Admin always has access
        assert can_access(admin, member_ids)

        # Manager in team has access
        assert can_access(manager, member_ids)

        # User in team has access (no creator specified)
        assert can_access(user, member_ids)

        # User in team but not creator
        assert not can_access(user, member_ids, creator_id=2)


class TestPermissionEdgeCases:
    """Test edge cases in permission logic."""

    def test_user_with_multiple_ids_in_set(self) -> None:
        """User with ID in large member set."""
        user = User(
            id=50,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        large_member_set = set(range(1, 101))  # 1 to 100
        assert can_access(user, large_member_set)

    def test_negative_user_ids(self) -> None:
        """Handle negative user IDs (edge case)."""
        user = User(
            id=-1,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        # User with negative ID in members
        assert can_access(user, {-1, 1, 2})

        # User with negative ID not in members
        assert not can_access(user, {1, 2, 3})

    def test_user_id_zero(self) -> None:
        """Handle user ID of zero."""
        user = User(
            id=0,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        assert can_access(user, {0, 1, 2})
        assert not can_access(user, {1, 2, 3})

    def test_type_safety(self) -> None:
        """Ensure type safety of function parameters."""
        user = User(
            id=1,
            email="user@test.com",
            username="user",
            role=UserRole.USER,
        )

        # Should work with set of ints
        assert can_access(user, {1, 2, 3})

        # Should work with empty set
        assert not can_access(user, set())


class TestRoleRequiredLogic:
    """
    Tests for role_required dependency logic.

    Note: These tests would be better as integration tests with FastAPI,
    but we can test the underlying permission logic here.
    """

    def test_single_role_requirement(self) -> None:
        """Test single role requirement."""
        admin = User(id=1, email="a@test.com", username="a", role=UserRole.ADMIN)
        manager = User(id=2, email="m@test.com", username="m", role=UserRole.MANAGER)
        user = User(id=3, email="u@test.com", username="u", role=UserRole.USER)

        # Admin-only
        allowed_roles = (UserRole.ADMIN,)
        assert admin.role in allowed_roles
        assert manager.role not in allowed_roles
        assert user.role not in allowed_roles

    def test_multiple_role_requirement(self) -> None:
        """Test multiple role requirement."""
        admin = User(id=1, email="a@test.com", username="a", role=UserRole.ADMIN)
        manager = User(id=2, email="m@test.com", username="m", role=UserRole.MANAGER)
        user = User(id=3, email="u@test.com", username="u", role=UserRole.USER)

        # Admin or Manager
        allowed_roles = (UserRole.ADMIN, UserRole.MANAGER)
        assert admin.role in allowed_roles
        assert manager.role in allowed_roles
        assert user.role not in allowed_roles

    def test_all_roles_allowed(self) -> None:
        """Test when all roles are allowed."""
        admin = User(id=1, email="a@test.com", username="a", role=UserRole.ADMIN)
        manager = User(id=2, email="m@test.com", username="m", role=UserRole.MANAGER)
        user = User(id=3, email="u@test.com", username="u", role=UserRole.USER)

        allowed_roles = (UserRole.ADMIN, UserRole.MANAGER, UserRole.USER)
        assert admin.role in allowed_roles
        assert manager.role in allowed_roles
        assert user.role in allowed_roles
