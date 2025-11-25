from starlette import status

from app.errors.schemas import APIErrorSchema


class APIError(Exception):
    """Base class for all API exceptions."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "bad_request"
    message: str = "Something went wrong"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message

    def to_pydantic(self) -> APIErrorSchema:
        """Convert the exception into a Pydantic error schema."""
        return APIErrorSchema(
            error_code=self.error_code,
            message=self.message,
        )


class ForbiddenAccessError(APIError):
    """Raised when a user attempts an action they do not have permission for."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"
    message = "You don`t have permission to perform this action."


class ObjectExistsError(APIError):
    """Raised when attempting to create an object that already exists."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "object_exists"

    def __init__(self, object_name: str, message: str | None = None) -> None:
        super().__init__(message or f"{object_name} already exists")


class ObjectNotFoundError(APIError):
    """Raised when a requested object could not be found in the database."""

    status_code: int = status.HTTP_404_NOT_FOUND
    error_code: str = "object_not_found"

    def __init__(self, object_name: str, message: str | None = None) -> None:
        super().__init__(message or f"{object_name} not found")


class AlreadyInTeamError(APIError):
    """Raised when a user tries to join a team but is already in another team."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "already_in_team"
    message: str = "You are already in a team."


class NotInTeamError(APIError):
    """Raised when a user tries to leave a team they are not a member of."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "not_in_team"
    message: str = "You are not in this team."


class TaskNotCompletedError(APIError):
    """Raised when trying to evaluate a non-completed task."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "task_not_completed"
    message: str = "Task must be completed to be evaluated"


class EvaluationAlreadyExistsError(APIError):
    """Raised when task already has an evaluation."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "evaluation_exists"
    message: str = "Task already has an evaluation"


class InvalidAssigneeError(APIError):
    """Raised when assignee is not from the same team."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "invalid_assignee"
    message: str = "Assignee must be from the task's team"
