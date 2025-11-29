from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.association import user_team

if TYPE_CHECKING:
    from app.models.meeting import Meeting
    from app.models.task import Task
    from app.models.user import User


class Team(Base):
    """
    Represents a team that users can belong to.

    Attributes:
        name (str): Unique name of the team.
        invite_code (str): Invite code for the team.
        members (list[User]): List of users who are part of this team.
    """

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    invite_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    members: Mapped[list["User"]] = relationship("User", secondary=user_team, back_populates="teams")

    meetings: Mapped[list["Meeting"]] = relationship(
        "Meeting",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="team",
        cascade="all, delete-orphan",
    )
