# mypy: ignore-errors

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication.strategy import DatabaseStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin.filters import AllUniqueStringValuesFilter, BooleanFilter, StaticValuesFilter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.requests import Request

from app.authentication.user_manager import UserManager
from app.core.config import settings
from app.core.db_helper import db_helper
from app.models import AccessToken, Comment, Evaluation, Meeting, Task, Team, User
from app.models.task import TaskStatus
from app.models.user import UserRole


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(secret_key=secret_key)
        self.session_factory = session_factory

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        async with self.session_factory() as session:
            user_db: SQLAlchemyUserDatabase[User, int] = SQLAlchemyUserDatabase(session, User)
            user_manager = UserManager(user_db)

            credentials = OAuth2PasswordRequestForm(username=email, password=password, scope="")  # type: ignore[arg-type]
            user = await user_manager.authenticate(credentials)

            if not user:
                return False

            if not (getattr(user, "role", None) == UserRole.ADMIN or user.is_superuser):
                return False

            access_token_db: SQLAlchemyAccessTokenDatabase[AccessToken] = SQLAlchemyAccessTokenDatabase(
                session,
                type[AccessToken],
            )
            strategy: DatabaseStrategy[User, int, AccessToken] = DatabaseStrategy(
                database=access_token_db,
                lifetime_seconds=settings.access_token.lifetime_seconds,
            )

            token_response = await strategy.write_token(user)

            request.session["token"] = token_response

        return True

    async def logout(self, request: Request) -> bool:
        token = request.session.get("token")

        if token:
            async with self.session_factory() as session:
                access_token_db = SQLAlchemyAccessTokenDatabase(session, AccessToken)
                strategy: DatabaseStrategy[User, int, AccessToken] = DatabaseStrategy(
                    database=access_token_db,
                    lifetime_seconds=settings.access_token.lifetime_seconds,
                )
                await strategy.destroy_token(token, None)

        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        async with self.session_factory() as session:
            user_db: SQLAlchemyUserDatabase[User, int] = SQLAlchemyUserDatabase(session, User)
            user_manager = UserManager(user_db)

            access_token_db = SQLAlchemyAccessTokenDatabase(session, AccessToken)
            strategy: DatabaseStrategy = DatabaseStrategy(
                database=access_token_db,
                lifetime_seconds=settings.access_token.lifetime_seconds,
            )

            user = await strategy.read_token(token, user_manager)

            if not user:
                request.session.clear()
                return False

            return getattr(user, "role", None) == UserRole.ADMIN or user.is_superuser


class UserAdmin(ModelView, model=User):
    """Admin view for User model."""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_list = [
        "id",
        "username",
        "email",
        "role",
        "is_active",
        "is_verified",
        "created_at",
    ]

    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email, User.created_at]
    column_default_sort = [(User.created_at, True)]

    form_excluded_columns = [User.hashed_password, User.created_at, User.updated_at]

    column_filters = [
        StaticValuesFilter(
            User.role,
            values=[(role.value, role.name) for role in UserRole],
        ),
        BooleanFilter("is_active"),
    ]

    column_details_list = [
        "id",
        "username",
        "email",
        "role",
        "is_active",
        "is_verified",
        "is_superuser",
        "created_at",
        "updated_at",
    ]

    column_labels = {
        User.id: "ID",
        User.username: "Username",
        User.email: "Email",
        User.role: "Role",
        User.is_active: "Active",
        User.is_verified: "Verified",
        User.is_superuser: "Superuser",
        User.created_at: "Created",
        User.updated_at: "Updated",
    }

    column_formatters = {
        User.role: lambda m, a: m.role.value if m.role else None,
        User.is_active: lambda m, a: "✅" if m.is_active else "❌",
        User.is_verified: lambda m, a: "✅" if m.is_verified else "❌",
    }


class TeamAdmin(ModelView, model=Team):
    """Admin view for Team model."""

    name = "Team"
    name_plural = "Teams"
    icon = "fa-solid fa-users"

    column_list = [
        Team.id,
        Team.name,
        Team.invite_code,
        Team.created_at,
    ]

    column_searchable_list = [Team.name, Team.invite_code]
    column_sortable_list = [Team.id, Team.name, Team.created_at]
    column_default_sort = [(Team.created_at, True)]

    column_details_list = [
        Team.id,
        Team.name,
        Team.invite_code,
        Team.created_at,
        Team.updated_at,
    ]

    column_labels = {
        Team.id: "ID",
        Team.name: "Team Name",
        Team.invite_code: "Invite Code",
        Team.created_at: "Created",
        Team.updated_at: "Updated",
    }


class TaskAdmin(ModelView, model=Task):
    """Admin view for Task model."""

    name = "Task"
    name_plural = "Tasks"
    icon = "fa-solid fa-tasks"

    column_list = [
        Task.id,
        Task.title,
        Task.status,
        Task.deadline,
        Task.team_id,
        Task.assignee_id,
        Task.created_at,
    ]

    column_searchable_list = [Task.title, Task.description]
    column_sortable_list = [
        Task.id,
        Task.title,
        Task.status,
        Task.deadline,
        Task.created_at,
    ]
    column_default_sort = [(Task.created_at, True)]

    column_filters = [
        StaticValuesFilter(
            Task.status,
            values=[(status.value, status.name) for status in TaskStatus],
        ),
        AllUniqueStringValuesFilter("team_id"),
        AllUniqueStringValuesFilter("creator_id"),
        AllUniqueStringValuesFilter("assignee_id"),
    ]

    column_details_list = [
        Task.id,
        Task.title,
        Task.description,
        Task.status,
        Task.deadline,
        Task.team_id,
        Task.creator_id,
        Task.assignee_id,
        Task.created_at,
        Task.updated_at,
    ]

    column_labels = {
        Task.id: "ID",
        Task.title: "Title",
        Task.description: "Description",
        Task.status: "Status",
        Task.deadline: "Deadline",
        Task.team_id: "Team",
        Task.creator_id: "Creator",
        Task.assignee_id: "Assignee",
        Task.created_at: "Created",
        Task.updated_at: "Updated",
    }

    column_formatters = {
        Task.status: lambda m, a: m.status.value if m.status else None,
        Task.deadline: lambda m, a: m.deadline.strftime("%Y-%m-%d %H:%M") if m.deadline else "No deadline",
    }


class CommentAdmin(ModelView, model=Comment):
    """Admin view for Comment model."""

    name = "Comment"
    name_plural = "Comments"
    icon = "fa-solid fa-comment"

    column_list = [
        Comment.id,
        Comment.content,
        Comment.task_id,
        Comment.author_id,
        Comment.created_at,
    ]

    column_searchable_list = [Comment.content]
    column_sortable_list = [Comment.id, Comment.created_at]
    column_default_sort = [(Comment.created_at, True)]

    column_filters = [
        AllUniqueStringValuesFilter("task_id"),
        AllUniqueStringValuesFilter("author_id"),
    ]

    column_details_list = [
        Comment.id,
        Comment.content,
        Comment.task_id,
        Comment.author_id,
        Comment.created_at,
        Comment.updated_at,
    ]

    column_labels = {
        Comment.id: "ID",
        Comment.content: "Content",
        Comment.task_id: "Task",
        Comment.author_id: "Author",
        Comment.created_at: "Created",
        Comment.updated_at: "Updated",
    }

    column_formatters = {
        Comment.content: lambda m, a: (m.content[:50] + "...") if len(m.content) > 50 else m.content,
    }


class EvaluationAdmin(ModelView, model=Evaluation):
    """Admin view for Evaluation model."""

    name = "Evaluation"
    name_plural = "Evaluations"
    icon = "fa-solid fa-star"

    column_list = [
        Evaluation.id,
        Evaluation.rating,
        Evaluation.task_id,
        Evaluation.created_at,
    ]

    column_sortable_list = [
        Evaluation.id,
        Evaluation.rating,
        Evaluation.created_at,
    ]
    column_default_sort = [(Evaluation.created_at, True)]

    column_filters = [
        AllUniqueStringValuesFilter("rating"),
        AllUniqueStringValuesFilter("task_id"),
    ]

    column_details_list = [
        Evaluation.id,
        Evaluation.rating,
        Evaluation.task_id,
        Evaluation.created_at,
        Evaluation.updated_at,
    ]

    column_labels = {
        Evaluation.id: "ID",
        Evaluation.rating: "Rating",
        Evaluation.task_id: "Task",
        Evaluation.created_at: "Created",
        Evaluation.updated_at: "Updated",
    }

    column_formatters = {
        Evaluation.rating: lambda m, a: "⭐" * m.rating,
    }


class MeetingAdmin(ModelView, model=Meeting):
    """Admin view for Meeting model."""

    name = "Meeting"
    name_plural = "Meetings"
    icon = "fa-solid fa-calendar"

    column_list = [
        Meeting.id,
        Meeting.title,
        Meeting.start_time,
        Meeting.end_time,
        Meeting.team_id,
        Meeting.organizer_id,
        Meeting.created_at,
    ]

    column_searchable_list = [Meeting.title, Meeting.description]
    column_sortable_list = [
        Meeting.id,
        Meeting.title,
        Meeting.start_time,
        Meeting.created_at,
    ]
    column_default_sort = [(Meeting.start_time, False)]

    column_filters = [
        AllUniqueStringValuesFilter("team_id"),
        AllUniqueStringValuesFilter("organizer_id"),
        AllUniqueStringValuesFilter("start_time"),
    ]

    column_details_list = [
        Meeting.id,
        Meeting.title,
        Meeting.description,
        Meeting.start_time,
        Meeting.end_time,
        Meeting.team_id,
        Meeting.organizer_id,
        Meeting.created_at,
        Meeting.updated_at,
    ]

    column_labels = {
        Meeting.id: "ID",
        Meeting.title: "Title",
        Meeting.description: "Description",
        Meeting.start_time: "Start Time",
        Meeting.end_time: "End Time",
        Meeting.team_id: "Team",
        Meeting.organizer_id: "Organizer",
        Meeting.created_at: "Created",
        Meeting.updated_at: "Updated",
    }

    column_formatters = {
        Meeting.start_time: lambda m, a: m.start_time.strftime("%Y-%m-%d %H:%M"),
        Meeting.end_time: lambda m, a: m.end_time.strftime("%Y-%m-%d %H:%M"),
    }


def setup_admin(app, engine) -> Admin:
    """
    Configure and mount admin panel to the application.

    Args:
        app: FastAPI application instance
        engine: SQLAlchemy async engine

    Returns:
        Admin: Configured admin instance
    """
    authentication_backend = AdminAuth(
        secret_key=settings.access_token.verification_token_secret,
        session_factory=db_helper.session_factory,
    )

    admin = Admin(
        app=app,
        engine=engine,
        title="Business Management System",
        authentication_backend=authentication_backend,
    )

    admin.add_view(UserAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(CommentAdmin)
    admin.add_view(EvaluationAdmin)
    admin.add_view(MeetingAdmin)

    return admin
