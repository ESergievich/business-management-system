from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models import (
        Task,
    )


class Evaluation(Base):
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One evaluation per task
        index=True,
    )
    task: Mapped["Task"] = relationship("Task", back_populates="evaluation")

    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),)
