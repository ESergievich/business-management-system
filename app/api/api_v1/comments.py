from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from app.authentication.fastapi_users_object import current_active_user
from app.core.config import settings
from app.core.db_helper import db_helper
from app.core.permissions import can_access
from app.errors.exceptions import ForbiddenAccessError, ObjectNotFoundError
from app.models import Comment, Task, Team, User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate

router = APIRouter(prefix=settings.api.v1.comments, tags=["Comments"])


@router.post(
    "/",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment on a task",
    description="""
    Creates a comment on a task. Only team members can comment.
    """,
)
async def create_comment(
    task_id: int,
    comment_data: CommentCreate,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Comment:
    result = await session.execute(
        select(Task).where(Task.id == task_id).options(joinedload(Task.team).selectinload(Team.members)),
    )
    task = result.scalar_one_or_none()

    if not task:
        msg = "Task"
        raise ObjectNotFoundError(msg)

    if current_user not in task.team.members:
        raise ForbiddenAccessError

    comment = Comment(
        content=comment_data.content,
        author_id=current_user.id,
        task_id=task_id,
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


@router.get(
    "/",
    response_model=list[CommentRead],
    summary="Get all comments for a task",
    description="Returns all comments for the specified task, ordered by creation time.",
)
async def get_comments(
    task_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Sequence[Comment]:
    result = await session.execute(select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at))
    return result.scalars().all()


@router.patch(
    "/{comment_id}",
    response_model=CommentRead,
    summary="Update a comment",
    description="Updates a comment. Only the author can update their own comments.",
)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Comment:
    comment: Comment | None = await session.get(Comment, comment_id)
    if not comment:
        msg = "Comment"
        raise ObjectNotFoundError(msg)

    if comment.author_id != current_user.id:
        raise ForbiddenAccessError

    comment.content = comment_data.content
    await session.commit()
    await session.refresh(comment)
    return comment


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    description="""
    Deletes a comment. Access is granted to:
    - Admins (full access)
    - Managers in the task's team
    - Comment author
    """,
)
async def delete_comment(
    comment_id: int,
    current_user: Annotated[User, Depends(current_active_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> None:
    result = await session.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(joinedload(Comment.task).joinedload(Task.team).selectinload(Team.members)),
    )
    comment: Comment | None = result.scalar_one_or_none()

    if not comment:
        msg = "Comment"
        raise ObjectNotFoundError(msg)

    member_ids = {member.id for member in comment.task.team.members}

    if not can_access(current_user, member_ids, creator_id=comment.author_id):
        raise ForbiddenAccessError

    await session.delete(comment)
    await session.commit()
