import secrets
from typing import Annotated, cast

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.authentication.fastapi_users_object import current_active_user
from app.core.config import settings
from app.core.db_helper import db_helper
from app.dependencies.role_dependencies import role_required
from app.errors.exceptions import (
    AlreadyInTeamError,
    ForbiddenAccessError,
    NotInTeamError,
    ObjectExistsError,
    ObjectNotFoundError,
)
from app.models import User
from app.models.team import Team
from app.models.user import UserRole
from app.schemas.team import TeamCreate, TeamCreateRead, TeamJoin, TeamRead

router = APIRouter(prefix=settings.api.v1.teams, tags=["Teams"])


@router.post(
    "",
    response_model=TeamCreateRead,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new team",
    description="Allows an admin to create a new team with a unique invite code.",
)
async def create_team(
    team_data: TeamCreate,
    _current_user: Annotated[User, Depends(role_required(UserRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Team:
    result = await session.execute(select(Team).where(Team.name == team_data.name))
    existing_team = result.scalar_one_or_none()

    if existing_team:
        raise ObjectExistsError(
            object_name="Team",
        )

    invite_code = secrets.token_urlsafe(8)
    new_team = Team(
        name=team_data.name,
        invite_code=invite_code,
    )

    session.add(new_team)
    await session.commit()
    await session.refresh(new_team)
    return new_team


@router.post(
    "/join",
    response_model=TeamRead,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="Join a team",
    description="Allows the current user to join a team using an invite code.",
)
async def join_team(
    join_data: TeamJoin,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Team:
    result = await session.execute(
        select(Team).where(Team.invite_code == join_data.invite_code).options(selectinload(Team.members)),
    )
    team = result.scalar_one_or_none()

    if not team:
        msg = "Team"
        raise ObjectNotFoundError(msg)

    if current_user in team.members:
        raise AlreadyInTeamError

    team.members.append(current_user)
    await session.commit()
    return team


@router.delete(
    "/{team_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave a team",
    description="Allows the current user to leave a team they are a member of.",
)
async def leave_team(
    team_id: int,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> None:
    """
    Leave a team.

    Args:
        team_id (int): ID of the team to leave.
        current_user (User): Current authenticated user.
        session (AsyncSession): Database session.

    Raises:
        NotInTeamException: If the user is not part of the specified team.
    """
    result = await session.execute(
        select(Team).where(Team.id == team_id),
    )
    team = result.scalar_one_or_none()

    if not team or current_user not in team.members:
        raise NotInTeamError

    team.members.remove(current_user)
    session.add(team)
    await session.commit()


@router.get(
    "/{team_id}/members",
    response_model=TeamRead,
    summary="Get team members",
    description="Allows an admin or manager to view the members of a team.",
)
async def get_team_members(
    team_id: int,
    _current_user: Annotated[User, Depends(role_required(UserRole.ADMIN, UserRole.MANAGER))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Team:
    result = await session.execute(select(Team).where(Team.id == team_id).options(selectinload(Team.members)))
    team = result.scalar_one_or_none()

    if not team:
        msg = "Team"
        raise ObjectNotFoundError(msg)

    return team


@router.post(
    "/{team_id}/members/{user_id}",
    response_model=TeamRead,
    summary="Add a user to a team",
    description="Allows an admin to add any user to a team. A manager can add users only to their own team.",
)
async def add_team_member(
    team_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(role_required(UserRole.ADMIN, UserRole.MANAGER))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Team:
    result = await session.execute(
        select(Team).where(Team.id == team_id).options(selectinload(Team.members)),
    )
    team = result.scalar_one_or_none()
    if not team:
        msg = "Team"
        raise ObjectNotFoundError(msg)

    result = await session.execute(select(User).where(User.id == user_id))
    user = cast("User | None", result.scalar_one_or_none())
    if not user:
        msg = "User"
        raise ObjectNotFoundError(msg)

    if current_user.role == UserRole.MANAGER and current_user not in team.members:
        msg = "Managers can only manage their own team members."
        raise ForbiddenAccessError(msg)

    if user in team.members:
        raise AlreadyInTeamError

    team.members.append(user)
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


@router.delete(
    "/{team_id}/members/{user_id}",
    response_model=TeamRead,
    summary="Remove a user from a team",
    description=(
        "Allows an admin to remove any user from a team. A manager can remove users only from their own team."
    ),
)
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(role_required(UserRole.ADMIN, UserRole.MANAGER))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Team:
    result = await session.execute(
        select(Team).where(Team.id == team_id).options(selectinload(Team.members)),
    )
    team = result.scalar_one_or_none()
    if not team:
        msg = "Team"
        raise ObjectNotFoundError(msg)

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        msg = "User"
        raise ObjectNotFoundError(msg)

    if current_user.role == UserRole.MANAGER and current_user not in team.members:
        msg = "Managers can only manage their own team members."
        raise ForbiddenAccessError(msg)

    if user not in team.members:  # type: ignore[comparison-overlap]
        raise NotInTeamError

    team.members.remove(user)  # type: ignore[arg-type]
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team
