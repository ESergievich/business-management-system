"""
create Meeting model.

Revision ID: ad7e067eec55
Revises: 8e31e39fdebe
Create Date: 2025-11-27 01:33:07.006439

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ad7e067eec55"
down_revision: str | Sequence[str] | None = "8e31e39fdebe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "meetings",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("organizer_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("end_time > start_time", name=op.f("ck_meetings_meeting_time_range")),
        sa.ForeignKeyConstraint(
            ["organizer_id"],
            ["users.id"],
            name=op.f("fk_meetings_organizer_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_meetings_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meetings")),
    )
    op.create_index(op.f("ix_meetings_created_at"), "meetings", ["created_at"], unique=False)
    op.create_index(op.f("ix_meetings_end_time"), "meetings", ["end_time"], unique=False)
    op.create_index(op.f("ix_meetings_organizer_id"), "meetings", ["organizer_id"], unique=False)
    op.create_index(op.f("ix_meetings_start_time"), "meetings", ["start_time"], unique=False)
    op.create_index(op.f("ix_meetings_updated_at"), "meetings", ["updated_at"], unique=False)
    op.create_table(
        "meeting_participants",
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name=op.f("fk_meeting_participants_meeting_id_meetings"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_meeting_participants_user_id_users")),
        sa.PrimaryKeyConstraint("meeting_id", "user_id", name=op.f("pk_meeting_participants")),
    )
    op.drop_constraint(op.f("fk_user_team_team_id_teams"), "user_team", type_="foreignkey")
    op.drop_constraint(op.f("fk_user_team_user_id_users"), "user_team", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_user_team_team_id_teams"),
        "user_team",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_user_team_user_id_users"),
        "user_team",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("fk_user_team_user_id_users"), "user_team", type_="foreignkey")
    op.drop_constraint(op.f("fk_user_team_team_id_teams"), "user_team", type_="foreignkey")
    op.create_foreign_key(op.f("fk_user_team_user_id_users"), "user_team", "users", ["user_id"], ["id"])
    op.create_foreign_key(op.f("fk_user_team_team_id_teams"), "user_team", "teams", ["team_id"], ["id"])
    op.drop_table("meeting_participants")
    op.drop_index(op.f("ix_meetings_updated_at"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_start_time"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_organizer_id"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_end_time"), table_name="meetings")
    op.drop_index(op.f("ix_meetings_created_at"), table_name="meetings")
    op.drop_table("meetings")
    # ### end Alembic commands ###
