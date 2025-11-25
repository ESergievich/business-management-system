from pydantic import BaseModel, ConfigDict, Field


class EvaluationCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")


class EvaluationRead(EvaluationCreate):
    task_id: int

    model_config = ConfigDict(from_attributes=True)
