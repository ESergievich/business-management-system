from enum import Enum
from typing import TYPE_CHECKING

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Enum as SQLA_Enum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.association import user_team
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.task import Task
    from app.models.team import Team


class UserRole(str, Enum):
    """
    UserRole defines the possible roles a user can have in the system.

    Attributes:
        USER: Regular user with limited permissions.
        MANAGER: User with elevated permissions to manage certain resources.
        ADMIN: Superuser with full access.
    """

    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class User(Base, SQLAlchemyBaseUserTable[int]):
    """
    User model represents a system user.

    Inherits from SQLAlchemyBaseUserTable to integrate with FastAPI Users.
    Contains additional fields for username and role.

    Attributes:
        username (str): Unique username of the user.
        role (UserRole): Role of the user, default is `USER`.
        teams (list[Team]): List of teams the user belongs to.
    """

    username: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLA_Enum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )

    teams: Mapped[list["Team"]] = relationship("Team", secondary=user_team, back_populates="members")

    created_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        foreign_keys="Task.creator_id",
        back_populates="creator",
        cascade="all",
    )

    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assignee_id",
        back_populates="assignee",
        cascade="all",
    )

    # Comments by this user (SET NULL on delete)
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all",
    )
