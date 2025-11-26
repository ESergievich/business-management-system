"""
create Comment Evaluation Task models.

Revision ID: 8e31e39fdebe
Revises: 7b99f6fdbf86
Create Date: 2025-11-26 00:10:38.847346

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e31e39fdebe"
down_revision: str | Sequence[str] | None = "7b99f6fdbf86"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tasks",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("OPEN", "IN_PROGRESS", "COMPLETED", name="taskstatus"), nullable=False),
        sa.Column("deadline", sa.DateTime(), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name=op.f("fk_tasks_assignee_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["users.id"],
            name=op.f("fk_tasks_creator_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_tasks_team_id_teams"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(op.f("ix_tasks_assignee_id"), "tasks", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_tasks_created_at"), "tasks", ["created_at"], unique=False)
    op.create_index(op.f("ix_tasks_creator_id"), "tasks", ["creator_id"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_updated_at"), "tasks", ["updated_at"], unique=False)
    op.create_table(
        "comments",
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_comments_author_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name=op.f("fk_comments_task_id_tasks"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comments")),
    )
    op.create_index(op.f("ix_comments_author_id"), "comments", ["author_id"], unique=False)
    op.create_index(op.f("ix_comments_created_at"), "comments", ["created_at"], unique=False)
    op.create_index(op.f("ix_comments_task_id"), "comments", ["task_id"], unique=False)
    op.create_index(op.f("ix_comments_updated_at"), "comments", ["updated_at"], unique=False)
    op.create_table(
        "evaluations",
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name=op.f("ck_evaluations_rating_range")),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_evaluations_task_id_tasks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluations")),
    )
    op.create_index(op.f("ix_evaluations_created_at"), "evaluations", ["created_at"], unique=False)
    op.create_index(op.f("ix_evaluations_task_id"), "evaluations", ["task_id"], unique=True)
    op.create_index(op.f("ix_evaluations_updated_at"), "evaluations", ["updated_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_evaluations_updated_at"), table_name="evaluations")
    op.drop_index(op.f("ix_evaluations_task_id"), table_name="evaluations")
    op.drop_index(op.f("ix_evaluations_created_at"), table_name="evaluations")
    op.drop_table("evaluations")
    op.drop_index(op.f("ix_comments_updated_at"), table_name="comments")
    op.drop_index(op.f("ix_comments_task_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_created_at"), table_name="comments")
    op.drop_index(op.f("ix_comments_author_id"), table_name="comments")
    op.drop_table("comments")
    op.drop_index(op.f("ix_tasks_updated_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_creator_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_created_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_assignee_id"), table_name="tasks")
    op.drop_table("tasks")
