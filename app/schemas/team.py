from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import UserRead


class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate that the name is not empty."""
        if not v or not v.strip():
            msg = "Team name cannot be empty"
            raise ValueError(msg)
        return v.strip()


class TeamRead(TeamBase):
    id: int
    invite_code: str | None = None
    members: list[UserRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TeamUpdate(BaseModel):
    name: str | None


class TeamJoin(BaseModel):
    invite_code: str
