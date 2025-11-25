from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models import Comment, Evaluation, Team, User


class TaskStatus(str, Enum):
    """Статусы задачи."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Task(Base):
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.OPEN,
        nullable=False,
        index=True,
    )
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    team: Mapped["Team"] = relationship("Team", back_populates="tasks")

    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    creator: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="created_tasks",
    )

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assignee_id],
        back_populates="assigned_tasks",
    )

    evaluation: Mapped["Evaluation | None"] = relationship(
        "Evaluation",
        back_populates="task",
        cascade="all, delete-orphan",
        uselist=False,
    )

    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )
