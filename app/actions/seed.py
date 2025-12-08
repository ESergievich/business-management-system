"""
Скрипт для заполнения базы данных тестовыми данными.

Создает:
- 3 пользователя (admin, manager, user)
- 2 команды
- Задачи с различными статусами
- Встречи
- Оценки выполненных задач
- Комментарии к задачам

Использование:
    python seed_database.py
"""

import asyncio
from datetime import datetime, timedelta

from fastapi_users.password import PasswordHelper
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.models import Comment, Evaluation, Meeting, Task, Team, User
from app.models.task import TaskStatus
from app.models.user import UserRole


async def clear_database(session: AsyncSession) -> None:
    """Очистка всех таблиц (опционально)."""
    # Удаляем в правильном порядке из-за foreign keys
    await session.execute(text("DELETE FROM evaluations"))
    await session.execute(text("DELETE FROM comments"))
    await session.execute(text("DELETE FROM meeting_participants"))
    await session.execute(text("DELETE FROM meetings"))
    await session.execute(text("DELETE FROM tasks"))
    await session.execute(text("DELETE FROM user_team"))
    await session.execute(text("DELETE FROM teams"))
    await session.execute(text("DELETE FROM access_tokens"))
    await session.execute(text("DELETE FROM users"))

    await session.commit()


ph = PasswordHelper()


async def create_users(session: AsyncSession) -> dict[str, User]:
    """Создание тестовых пользователей."""
    users = {}

    # Admin
    admin = User(
        email="admin@test.com",
        username="Admin User",
        hashed_password=ph.hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    session.add(admin)
    users["admin"] = admin

    # Manager
    manager = User(
        email="manager@test.com",
        username="Manager User",
        hashed_password=ph.hash("manager123"),
        role=UserRole.MANAGER,
        is_active=True,
        is_verified=True,
    )
    session.add(manager)
    users["manager"] = manager

    # Regular User
    user = User(
        email="user@test.com",
        username="Regular User",
        hashed_password=ph.hash("user123"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    users["user"] = user

    # Additional users
    user2 = User(
        email="john@test.com",
        username="John Doe",
        hashed_password=ph.hash("password123"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    session.add(user2)
    users["user2"] = user2

    user3 = User(
        email="jane@test.com",
        username="Jane Smith",
        hashed_password=ph.hash("password123"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    session.add(user3)
    users["user3"] = user3

    await session.commit()

    return users


async def create_teams(session: AsyncSession, users: dict[str, User]) -> dict[str, Team]:
    """Создание команд и добавление участников."""
    teams = {}

    # Development Team
    dev_team = Team(
        name="Development Team",
        invite_code="DEV2024TEAM",
    )
    dev_team.members.extend(
        [
            users["admin"],
            users["manager"],
            users["user"],
            users["user2"],
        ],
    )
    session.add(dev_team)
    teams["dev"] = dev_team

    # Marketing Team
    marketing_team = Team(
        name="Marketing Team",
        invite_code="MKT2024TEAM",
    )
    marketing_team.members.extend(
        [
            users["admin"],
            users["user2"],
            users["user3"],
        ],
    )
    session.add(marketing_team)
    teams["marketing"] = marketing_team

    await session.commit()

    return teams


async def create_tasks(
    session: AsyncSession,
    users: dict[str, User],
    teams: dict[str, Team],
) -> list[Task]:
    """Создание задач."""
    tasks = []
    now = datetime.now()

    # Development Team Tasks
    task1 = Task(
        title="Implement user authentication",
        description="Add JWT-based authentication system",
        status=TaskStatus.COMPLETED,
        deadline=now - timedelta(days=5),
        team_id=teams["dev"].id,
        creator_id=users["manager"].id,
        assignee_id=users["user"].id,
    )
    tasks.append(task1)

    task2 = Task(
        title="Create API documentation",
        description="Document all REST API endpoints using OpenAPI",
        status=TaskStatus.IN_PROGRESS,
        deadline=now + timedelta(days=3),
        team_id=teams["dev"].id,
        creator_id=users["manager"].id,
        assignee_id=users["user2"].id,
    )
    tasks.append(task2)

    task3 = Task(
        title="Fix bug in payment processing",
        description="Users report errors during checkout",
        status=TaskStatus.OPEN,
        deadline=now + timedelta(days=7),
        team_id=teams["dev"].id,
        creator_id=users["admin"].id,
        assignee_id=users["user"].id,
    )
    tasks.append(task3)

    task4 = Task(
        title="Setup CI/CD pipeline",
        description="Configure GitHub Actions for automated testing and deployment",
        status=TaskStatus.IN_PROGRESS,
        deadline=now + timedelta(days=10),
        team_id=teams["dev"].id,
        creator_id=users["manager"].id,
        assignee_id=users["user2"].id,
    )
    tasks.append(task4)

    task5 = Task(
        title="Database migration",
        description="Migrate from SQLite to PostgreSQL",
        status=TaskStatus.COMPLETED,
        deadline=now - timedelta(days=10),
        team_id=teams["dev"].id,
        creator_id=users["admin"].id,
        assignee_id=users["manager"].id,
    )
    tasks.append(task5)

    # Marketing Team Tasks
    task6 = Task(
        title="Launch social media campaign",
        description="Prepare content for Facebook, Twitter, and Instagram",
        status=TaskStatus.IN_PROGRESS,
        deadline=now + timedelta(days=5),
        team_id=teams["marketing"].id,
        creator_id=users["admin"].id,
        assignee_id=users["user3"].id,
    )
    tasks.append(task6)

    task7 = Task(
        title="Analyze Q4 metrics",
        description="Create report on user acquisition and retention",
        status=TaskStatus.OPEN,
        deadline=now + timedelta(days=14),
        team_id=teams["marketing"].id,
        creator_id=users["admin"].id,
        assignee_id=users["user2"].id,
    )
    tasks.append(task7)

    task8 = Task(
        title="Email newsletter design",
        description="Design template for monthly newsletter",
        status=TaskStatus.COMPLETED,
        deadline=now - timedelta(days=3),
        team_id=teams["marketing"].id,
        creator_id=users["admin"].id,
        assignee_id=users["user3"].id,
    )
    tasks.append(task8)

    session.add_all(tasks)
    await session.commit()

    return tasks


async def create_comments(
    session: AsyncSession,
    users: dict[str, User],
    tasks: list[Task],
) -> None:
    """Создание комментариев к задачам."""
    comments = [
        Comment(
            content="I've started working on this. Should be done by tomorrow.",
            task_id=tasks[1].id,
            author_id=users["user2"].id,
        ),
        Comment(
            content="Great work! The authentication looks solid.",
            task_id=tasks[0].id,
            author_id=users["manager"].id,
        ),
        Comment(
            content="Need more details about the payment gateway error logs.",
            task_id=tasks[2].id,
            author_id=users["user"].id,
        ),
        Comment(
            content="The campaign is performing well! We've gained 500 new followers.",
            task_id=tasks[5].id,
            author_id=users["user3"].id,
        ),
        Comment(
            content="Added the test cases. Ready for review.",
            task_id=tasks[3].id,
            author_id=users["user2"].id,
        ),
    ]

    session.add_all(comments)
    await session.commit()


async def create_evaluations(
    session: AsyncSession,
    tasks: list[Task],
) -> None:
    """Создание оценок для выполненных задач."""
    evaluations = []

    # Оцениваем только завершенные задачи
    for task in tasks:
        if task.status == TaskStatus.COMPLETED:
            rating = 5 if task.id % 2 == 0 else 4
            evaluation = Evaluation(
                rating=rating,
                task_id=task.id,
            )
            evaluations.append(evaluation)

    session.add_all(evaluations)
    await session.commit()


async def create_meetings(
    session: AsyncSession,
    users: dict[str, User],
    teams: dict[str, Team],
) -> None:
    """Создание встреч."""
    now = datetime.now()
    meetings = []

    # Daily standup (сегодня)
    meeting1 = Meeting(
        title="Daily Standup",
        description="Quick sync on current progress and blockers",
        start_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
        end_time=now.replace(hour=10, minute=15, second=0, microsecond=0),
        team_id=teams["dev"].id,
        organizer_id=users["manager"].id,
    )
    meeting1.participants.extend(
        [
            users["manager"],
            users["user"],
            users["user2"],
        ],
    )
    meetings.append(meeting1)

    # Sprint planning (завтра)
    meeting2 = Meeting(
        title="Sprint Planning",
        description="Plan tasks for the next 2-week sprint",
        start_time=(now + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0),
        end_time=(now + timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0),
        team_id=teams["dev"].id,
        organizer_id=users["admin"].id,
    )
    meeting2.participants.extend(
        [
            users["admin"],
            users["manager"],
            users["user"],
            users["user2"],
        ],
    )
    meetings.append(meeting2)

    # Marketing review (через 3 дня)
    meeting3 = Meeting(
        title="Marketing Campaign Review",
        description="Review Q4 campaign performance",
        start_time=(now + timedelta(days=3)).replace(hour=15, minute=0, second=0, microsecond=0),
        end_time=(now + timedelta(days=3)).replace(hour=16, minute=30, second=0, microsecond=0),
        team_id=teams["marketing"].id,
        organizer_id=users["admin"].id,
    )
    meeting3.participants.extend(
        [
            users["admin"],
            users["user2"],
            users["user3"],
        ],
    )
    meetings.append(meeting3)

    # Team retrospective (прошлая неделя)
    meeting4 = Meeting(
        title="Sprint Retrospective",
        description="Discuss what went well and what to improve",
        start_time=now - timedelta(days=7),
        end_time=now - timedelta(days=7, hours=-1),
        team_id=teams["dev"].id,
        organizer_id=users["manager"].id,
    )
    meeting4.participants.extend(
        [
            users["manager"],
            users["user"],
            users["user2"],
        ],
    )
    meetings.append(meeting4)

    session.add_all(meetings)
    await session.commit()


async def seed_database() -> None:
    """Главная функция заполнения базы данных."""
    async with db_helper.session_factory() as session:
        # Опционально: очистить БД перед заполнением
        await clear_database(session)

        # Создаем данные
        users = await create_users(session)
        teams = await create_teams(session, users)
        tasks = await create_tasks(session, users, teams)
        await create_comments(session, users, tasks)
        await create_evaluations(session, tasks)
        await create_meetings(session, users, teams)


if __name__ == "__main__":
    asyncio.run(seed_database())
