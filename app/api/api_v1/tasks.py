from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status

from app.authentication.fastapi_users_object import current_active_user
from app.core.config import settings
from app.core.db_helper import db_helper
from app.core.permissions import can_access
from app.dependencies.role_dependencies import role_required
from app.errors.exceptions import ForbiddenAccessError, InvalidAssigneeError, ObjectNotFoundError
from app.models import Task, Team, User
from app.models.association import user_team
from app.models.user import UserRole
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix=settings.api.v1.tasks, tags=["Tasks"])


async def get_task_with_team(
    task_id: int,
    session: AsyncSession,
) -> Task:
    """Fetch a task with its team members loaded."""
    result = await session.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(
            joinedload(Task.team).selectinload(Team.members),
        ),
    )
    task = result.scalar_one_or_none()
    if not task:
        msg = "Task"
        raise ObjectNotFoundError(msg)
    return task


def validate_team_access(user: User, team_members: set[int]) -> None:
    """Validate user has access to the team."""
    if not can_access(user, team_members):
        raise ForbiddenAccessError


def validate_assignee_in_team(assignee_id: int | None, team_members: set[int]) -> None:
    """Validate assignee is from the team."""
    if assignee_id and assignee_id not in team_members:
        raise InvalidAssigneeError


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskRead,
    summary="Create a new task",
    description="""
    Creates a new task in a team. Only admins and managers can create tasks.
    Managers can only create tasks in teams they belong to.

    The assignee (if specified) must be a member of the target team.
    """,
)
async def create_task(
    task_data: TaskCreate,
    current_user: Annotated[User, Depends(role_required(UserRole.ADMIN, UserRole.MANAGER))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Task:
    result = await session.execute(select(Team).where(Team.id == task_data.team_id).options(selectinload(Team.members)))
    team = result.scalar_one_or_none()
    if not team:
        msg = "Team"
        raise ObjectNotFoundError(msg)

    member_ids = {member.id for member in team.members}

    if not can_access(current_user, member_ids):
        raise ForbiddenAccessError

    if task_data.assignee_id and task_data.assignee_id not in member_ids:
        raise InvalidAssigneeError

    task = Task(**task_data.model_dump(), creator_id=current_user.id)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update a task",
    description="""
    Updates an existing task. Access is granted to:
    - Admins (full access)
    - Managers in the task's team
    - Assignee (if they're a regular user in the team)

    If assignee_id is being updated, the new assignee must be from the same team.
    """,
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Task:
    task = await get_task_with_team(task_id, session)

    member_ids = {member.id for member in task.team.members}
    if not can_access(current_user, member_ids, task.assignee_id):
        raise ForbiddenAccessError

    if task_data.assignee_id and task_data.assignee_id not in member_ids:
        raise InvalidAssigneeError

    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    await session.commit()
    await session.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="""
    Deletes a task. Only admins and managers can delete tasks.
    Managers can only delete tasks in teams they belong to.

    Deleting a task will also delete all associated comments and evaluations.
    """,
)
async def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(role_required(UserRole.ADMIN, UserRole.MANAGER))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> None:
    task = await get_task_with_team(task_id, session)

    member_ids = {member.id for member in task.team.members}
    if not can_access(current_user, member_ids):
        raise ForbiddenAccessError

    await session.delete(task)
    await session.commit()


@router.get(
    "/",
    response_model=list[TaskRead],
    summary="List tasks",
    description="""
    Lists tasks based on user role:
    - Admins: see all tasks
    - Managers: see tasks from teams they belong to
    - Regular users: see tasks from teams they belong to
    """,
)
async def list_tasks(
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Sequence[Task]:
    if current_user.role == UserRole.ADMIN:
        result = await session.execute(select(Task))
        return result.scalars().all()

    stmt = (
        select(Task).join(user_team, user_team.c.team_id == Task.team_id).where(user_team.c.user_id == current_user.id)
    )

    result = await session.execute(stmt)
    return result.scalars().all()
