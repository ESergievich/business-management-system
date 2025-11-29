from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core.core_schema import FieldValidationInfo

from app.schemas.user import UserRead


class MeetingBase(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def end_time_after_start(cls, v: datetime, info: FieldValidationInfo) -> datetime:
        """Validate that end_time is after start_time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            msg = "End time must be after start time"
            raise ValueError(msg)
        return v


class MeetingCreate(MeetingBase):
    team_id: int
    participant_ids: list[int] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    participant_ids: list[int] | None = None

    @field_validator("end_time")
    @classmethod
    def end_time_after_start(cls, v: datetime | None, info: FieldValidationInfo) -> datetime | None:
        """Validate that end_time is after start_time if both are provided."""
        start_time = info.data.get("start_time")
        if v is not None and start_time is not None and v <= start_time:
            msg = "End time must be after start time"
            raise ValueError(msg)
        return v


class MeetingRead(MeetingBase):
    id: int
    team_id: int
    organizer_id: int | None = None
    participants: list[UserRead] = Field(default_factory=list, repr=False)
    participant_ids: list[int] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def extract_participant_ids(self) -> Self:
        """Extract participant IDs from participants list."""
        if hasattr(self, "participants") and self.participants:
            self.participant_ids = [p.id for p in self.participants]
        return self
