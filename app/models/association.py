from sqlalchemy import Column, ForeignKey, Table

from app.models import Base

user_team: Table = Table(
    "user_team",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("team_id", ForeignKey("teams.id"), primary_key=True),
)
