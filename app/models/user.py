from enum import Enum

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Enum as SQLA_Enum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


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
    """

    username: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLA_Enum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )
