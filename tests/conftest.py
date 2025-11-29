import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from datetime import datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import joinedload, selectinload

from app.authentication.fastapi_users_object import current_active_user
from app.core.db_helper import db_helper
from app.main import create_app
from app.models import Base, Comment, Evaluation, Meeting, Task, Team, User
from app.models.task import TaskStatus
from app.models.user import UserRole
from tests.helpers import unique_email, unique_string

# Test database URL - use in-memory SQLite or separate test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def create_test_app():
    return create_app()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,  # ← важно для in-memory!
        connect_args={"check_same_thread": False},  # для SQLite
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client_factory(
    test_session: AsyncSession,
) -> AsyncGenerator[Callable[[User], Coroutine[Any, Any, AsyncClient]], Any]:
    """Create test client with overridden database dependency."""
    clients = []

    async def factory(user: User) -> AsyncClient:
        app = create_test_app()

        async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
            yield test_session

        app.dependency_overrides[db_helper.session_getter] = override_get_session
        app.dependency_overrides[current_active_user] = lambda: user

        client = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test/api",
        )
        clients.append(client)
        return client

    yield factory
    # app.dependency_overrides.clear()
    for client in clients:
        await client.aclose()


# User fixtures
@pytest_asyncio.fixture(scope="function")
async def admin_user(test_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        email=unique_email("admin"),
        username="admin",
        role=UserRole.ADMIN,
        hashed_password="hashed_password",  # Replace with proper hashing
        is_active=True,
        is_verified=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def manager_user(test_session: AsyncSession) -> User:
    """Create a manager user."""
    user = User(
        email=unique_email("manager"),
        username="manager",
        role=UserRole.MANAGER,
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def regular_user(test_session: AsyncSession) -> User:
    """Create a regular user."""
    user = User(
        email=unique_email("user"),
        username="user",
        role=UserRole.USER,
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def another_user(test_session: AsyncSession) -> User:
    """Create another regular user for multi-user tests."""
    user = User(
        email=unique_email("another"),
        username="another",
        role=UserRole.USER,
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_client(client_factory, admin_user):
    client = await client_factory(admin_user)
    yield client
    # client._transport.app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def manager_client(client_factory, manager_user):
    client = await client_factory(manager_user)
    yield client
    # client._transport.app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def regular_client(client_factory, regular_user):
    client = await client_factory(regular_user)
    yield client
    # client._transport.app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def another_client(client_factory, another_user):
    client = await client_factory(another_user)
    yield client
    # client._transport.app.dependency_overrides.clear()


# Team fixtures
@pytest_asyncio.fixture(scope="function")
async def team(test_session: AsyncSession) -> Team:
    """Create a team."""
    team = Team(
        name=unique_string("TestTeam", length=6),
        invite_code=unique_string("CODE", length=8),
    )
    test_session.add(team)
    await test_session.commit()
    result = await test_session.execute(
        select(Team).options(selectinload(Team.members)).where(Team.id == team.id),
    )
    return result.scalar_one()


@pytest_asyncio.fixture
async def team_with_members(
    test_session: AsyncSession,
    team: Team,
    manager_user: User,
    regular_user: User,
) -> Team:
    """Create a team with members."""
    team.members.extend([manager_user, regular_user])
    test_session.add(team)
    await test_session.commit()
    await test_session.refresh(team)
    return team


# Task fixtures
@pytest_asyncio.fixture
async def task(
    test_session: AsyncSession,
    team_with_members: Team,
    manager_user: User,
    regular_user: User,
) -> Task:
    """Create a task."""
    task = Task(
        title="Test Task",
        description="Test task description",
        status=TaskStatus.OPEN,
        deadline=datetime.now() + timedelta(days=7),
        team_id=team_with_members.id,
        creator_id=manager_user.id,
        assignee_id=regular_user.id,
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def completed_task(
    test_session: AsyncSession,
    team_with_members: Team,
    manager_user: User,
    regular_user: User,
) -> Task:
    """Create a completed task."""
    task = Task(
        title="Completed Task",
        description="Completed task description",
        status=TaskStatus.COMPLETED,
        deadline=datetime.now() - timedelta(days=1),
        team_id=team_with_members.id,
        creator_id=manager_user.id,
        assignee_id=regular_user.id,
    )
    test_session.add(task)
    await test_session.commit()
    result = await test_session.execute(
        select(Task).where(Task.id == task.id).options(joinedload(Task.team).selectinload(Team.members)),
    )
    return result.scalar_one()


# Comment fixtures
@pytest_asyncio.fixture
async def comment(
    test_session: AsyncSession,
    task: Task,
    regular_user: User,
) -> Comment:
    """Create a comment."""
    comment = Comment(
        content="Test comment",
        task_id=task.id,
        author_id=regular_user.id,
    )
    test_session.add(comment)
    await test_session.commit()
    await test_session.refresh(comment)
    return comment


# Evaluation fixtures
@pytest_asyncio.fixture
async def evaluation(
    test_session: AsyncSession,
    completed_task: Task,
) -> Evaluation:
    """Create an evaluation."""
    evaluation = Evaluation(
        rating=5,
        task_id=completed_task.id,
    )
    test_session.add(evaluation)
    await test_session.commit()
    await test_session.refresh(evaluation)
    return evaluation


# Meeting fixtures
@pytest_asyncio.fixture
async def meeting(
    test_session: AsyncSession,
    team_with_members: Team,
    manager_user: User,
    regular_user: User,
) -> Meeting:
    """Create a meeting."""
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)

    meeting = Meeting(
        title="Test Meeting",
        description="Test meeting description",
        start_time=start_time,
        end_time=end_time,
        team_id=team_with_members.id,
        organizer_id=manager_user.id,
        participants=[manager_user, regular_user],
    )
    test_session.add(meeting)
    await test_session.commit()
    await test_session.refresh(meeting)
    return meeting


# Authentication helpers
def get_auth_headers(user: User) -> dict[str, str]:
    """
    Get authentication headers for a user.

    Note: This is a simplified version. In real tests, you should:
    1. Use proper JWT token generation
    2. Or mock the authentication dependency
    """
    return {"Authorization": f"Bearer {user.email}"}


@pytest.fixture
def mock_current_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock current_active_user dependency."""

    async def mock_user() -> User:
        # Return a mock user
        pass

    monkeypatch.setattr("app.core.dependencies.current_active_user", mock_user)
