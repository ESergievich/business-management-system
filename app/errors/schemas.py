from pydantic import BaseModel


class APIErrorSchema(BaseModel):
    error_code: str
    message: str
