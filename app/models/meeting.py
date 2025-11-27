from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.association import meeting_participants

if TYPE_CHECKING:
    from app.models import Team, User


class Meeting(Base):
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team: Mapped["Team"] = relationship("Team", back_populates="meetings")

    organizer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organizer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[organizer_id],
        back_populates="organized_meetings",
    )

    participants: Mapped[list["User"]] = relationship(
        "User",
        secondary=meeting_participants,
        back_populates="participating_meetings",
    )

    __table_args__ = (CheckConstraint("end_time > start_time", name="meeting_time_range"),)
