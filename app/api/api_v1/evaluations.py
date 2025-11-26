from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.authentication.fastapi_users_object import current_active_user
from app.core.config import settings
from app.core.db_helper import db_helper
from app.dependencies.role_dependencies import role_required
from app.errors.exceptions import (
    EvaluationAlreadyExistsError,
    ForbiddenAccessError,
    ObjectNotFoundError,
    TaskNotCompletedError,
)
from app.models.evaluation import Evaluation
from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationRead,
)

router = APIRouter(prefix=settings.api.v1.tasks, tags=["Evaluations"])


@router.post(
    "/{task_id}/evaluations",
    response_model=EvaluationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an evaluation for a completed task",
    description="""
    Creates an evaluation for a completed task. Only admins and managers can evaluate.
    Managers can only evaluate tasks from teams they belong to.

    Requirements:
    - Task must be in COMPLETED status
    - Task must not already have an evaluation
    - Rating must be between 1 and 5
    """,
)
async def create_evaluation(
    task_id: int,
    evaluation_data: EvaluationCreate,
    current_user: Annotated[User, Depends(role_required(UserRole.ADMIN, UserRole.MANAGER))],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Evaluation:
    result = await session.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(joinedload(Task.team).selectinload(Task.team.members), joinedload(Task.evaluation)),
    )
    task = result.scalar_one_or_none()
    if not task:
        msg = "Task"
        raise ObjectNotFoundError(msg)

    if current_user.role == UserRole.MANAGER and not any(current_user.id == member.id for member in task.team.members):
        raise ForbiddenAccessError

    if task.status != TaskStatus.COMPLETED:
        raise TaskNotCompletedError

    if task.evaluation is not None:
        raise EvaluationAlreadyExistsError

    new_evaluation = Evaluation(
        rating=evaluation_data.rating,
        task_id=task_id,
    )

    session.add(new_evaluation)
    await session.commit()
    await session.refresh(new_evaluation)
    return new_evaluation


@router.get(
    "/evaluations/me",
    response_model=list[EvaluationRead],
    summary="Get my evaluations",
    description="Returns all evaluations for tasks assigned to the current user.",
)
async def get_my_evaluations(
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Sequence[Evaluation]:
    result = await session.execute(
        select(Evaluation).join(Task).where(Task.assignee_id == current_user.id),
    )
    return result.scalars().all()


@router.get(
    "/evaluations/average/{user_id}",
    summary="Get average rating for a user",
    description="""
    Calculates the average rating for a user's completed tasks within a date range.

    Regular users can only view their own average rating.
    Admins and managers can view any user's average rating.
    """,
)
async def get_average_rating(
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: Annotated[User, Depends(current_active_user)],
) -> dict[str, float | None]:
    if current_user.role == UserRole.USER and current_user.id != user_id:
        raise ForbiddenAccessError

    result = await session.execute(
        select(func.avg(Evaluation.rating))
        .join(Task)
        .where(
            Task.assignee_id == user_id,
            Evaluation.created_at >= start_date,
            Evaluation.created_at <= end_date,
        ),
    )
    average = result.scalar()
    return {"user_id": user_id, "average_rating": float(average) if average else None}
