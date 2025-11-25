"""
create Team model.

Revision ID: 7b99f6fdbf86
Revises: f01d2d86b3d5
Create Date: 2025-11-21 01:31:00.337769

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b99f6fdbf86"
down_revision: str | Sequence[str] | None = "f01d2d86b3d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "teams",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("invite_code", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teams")),
        sa.UniqueConstraint("name", name=op.f("uq_teams_name")),
    )
    op.create_index(op.f("ix_teams_created_at"), "teams", ["created_at"], unique=False)
    op.create_index(op.f("ix_teams_invite_code"), "teams", ["invite_code"], unique=True)
    op.create_index(op.f("ix_teams_updated_at"), "teams", ["updated_at"], unique=False)
    op.create_table(
        "user_team",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_user_team_team_id_teams")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_team_user_id_users")),
        sa.PrimaryKeyConstraint("user_id", "team_id", name=op.f("pk_user_team")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_team")
    op.drop_index(op.f("ix_teams_updated_at"), table_name="teams")
    op.drop_index(op.f("ix_teams_invite_code"), table_name="teams")
    op.drop_index(op.f("ix_teams_created_at"), table_name="teams")
    op.drop_table("teams")
