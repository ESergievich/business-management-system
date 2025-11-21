from starlette import status

from app.errors.schemas import APIErrorSchema


class APIError(Exception):
    """
    Base class for all API exceptions.

    Args:
        message (str): The error message to be displayed.

    Returns:
        status_code: 400 BAD REQUEST
        error_code: "bad_request"
        message: Default message indicating something went wrong.
    """

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
    """
    Raised when a user attempts an action they do not have permission for.

    Returns:
        status_code: 403 FORBIDDEN
        error_code: "forbidden"
        message: Default message indicating lack of permission.
    """

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"
    message = "You don`t have permission to perform this action."


class ObjectExistsError(APIError):
    """
    Raised when attempting to create an object that already exists.

    Args:
        object_name (str): The name of the object that already exists.
        message (str | None): Optional custom error message.

    Returns:
        status_code: 400 BAD REQUEST
        error_code: "object_exists"
        message: Describes which object already exists.
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "object_exists"

    def __init__(self, object_name: str, message: str | None = None) -> None:
        super().__init__(message or f"{object_name} already exists")


class ObjectNotFoundError(APIError):
    """
    Raised when a requested object could not be found in the database.

    Args:
        object_name (str): The name of the missing object.
        message (str | None): Optional custom error message.

    Returns:
        status_code: 404 NOT FOUND
        error_code: "object_not_found"
        message: Describes which object was not found.
    """

    status_code: int = status.HTTP_404_NOT_FOUND
    error_code: str = "object_not_found"

    def __init__(self, object_name: str, message: str | None = None) -> None:
        super().__init__(message or f"{object_name} not found")


class AlreadyInTeamError(APIError):
    """
    Raised when a user tries to join a team but is already in another team.

    Attributes:
        status_code (int): 400 BAD REQUEST
        error_code (str): "already_in_team"
        message (str): Default message describing the conflict.
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "already_in_team"
    message: str = "You are already in a team."


class NotInTeamError(APIError):
    """
    Raised when a user tries to leave a team they are not a member of.

    Attributes:
        status_code (int): 400 BAD REQUEST
        error_code (str): "not_in_team"
        message (str): Default message indicating the user is not part of the team.
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "not_in_team"
    message: str = "You are not in this team."
