from fastapi_users import FastAPIUsers

from app.authentication.backend import authentication_backend
from app.authentication.dependencies import get_user_manager
from app.models.user import User

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [authentication_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
