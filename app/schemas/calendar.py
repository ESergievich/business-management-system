from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DateFilter(BaseModel):
    day: date | None = Field(
        None,
        description="Get events for this specific day",
        examples=["2024-01-15"],
    )
    month: date | None = Field(
        None,
        description="Get events for the month of this date (day is ignored)",
        examples=["2024-01-01"],
    )
    start: date | None = Field(
        None,
        description="Start date for custom range (requires end)",
        examples=["2024-01-01"],
    )
    end: date | None = Field(
        None,
        description="End date for custom range (requires start)",
        examples=["2024-01-31"],
    )

    @model_validator(mode="after")
    def validate_choice(self) -> Self:
        """Validate that exactly one filtering option is specified."""
        filled = [
            bool(self.day),
            bool(self.month),
            bool(self.start and self.end),
        ]

        if filled.count(True) != 1:
            msg = "Specify exactly one option: day, month, or period (start + end)"
            raise ValueError(msg)

        return self

    def get_period_type(self) -> Literal["day", "month", "range"]:
        """
        Get the type of period filter.

        Returns:
            "day" if filtering by day
            "month" if filtering by month
            "range" if filtering by custom range
        """
        if self.day:
            return "day"
        if self.month:
            return "month"
        return "range"


class TaskEventRead(BaseModel):
    """Task represented as a calendar event."""

    type: Literal["task"] = "task"
    id: int
    title: str
    description: str | None = None
    status: str
    deadline: datetime | None = None
    team_id: int
    creator_id: int | None = None
    assignee_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingEventRead(BaseModel):
    """Meeting represented as a calendar event."""

    type: Literal["meeting"] = "meeting"
    id: int
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    team_id: int
    organizer_id: int | None = None
    participant_ids: list[int] = []

    model_config = ConfigDict(from_attributes=True)


CalendarEvent = Annotated[
    TaskEventRead | MeetingEventRead,
    Field(discriminator="type"),
]


class CalendarEventRead(BaseModel):
    """
    Type-safe calendar events response using discriminated unions.

    This version provides better type safety and validation compared to CalendarEventRead.
    """

    start_period: datetime = Field(
        ...,
        description="Start of the period (inclusive)",
    )
    end_period: datetime = Field(
        ...,
        description="End of the period (exclusive)",
    )
    events: list[CalendarEvent] = Field(
        default_factory=list,
        description="List of events (tasks and meetings) sorted by time",
    )

    model_config = ConfigDict(from_attributes=True)
