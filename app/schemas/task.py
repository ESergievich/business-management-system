from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.task import TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    deadline: datetime | None = None
    status: TaskStatus = TaskStatus.OPEN


class TaskCreate(TaskBase):
    assignee_id: int | None = None
    team_id: int


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    deadline: datetime | None = None
    status: TaskStatus | None = None
    assignee_id: int | None = None


class TaskRead(TaskBase):
    id: int
    team_id: int
    creator_id: int | None = None
    assignee_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
