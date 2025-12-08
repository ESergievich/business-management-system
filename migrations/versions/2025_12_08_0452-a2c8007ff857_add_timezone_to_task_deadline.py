"""add timezone to task deadline

Revision ID: a2c8007ff857
Revises: ad7e067eec55
Create Date: 2025-12-08 04:52:21.089580

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a2c8007ff857'
down_revision: Union[str, Sequence[str], None] = 'ad7e067eec55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timezone to task deadline column."""
    # Конвертируем существующие данные, предполагая что они в UTC
    op.execute("""
        ALTER TABLE tasks 
        ALTER COLUMN deadline TYPE TIMESTAMP WITH TIME ZONE 
        USING deadline AT TIME ZONE 'UTC'
    """)

    op.execute("""
        ALTER TABLE tasks 
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
        USING created_at AT TIME ZONE 'UTC'
    """)

    op.execute("""
        ALTER TABLE tasks 
        ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE 
        USING updated_at AT TIME ZONE 'UTC'
    """)


def downgrade() -> None:
    """Remove timezone from task deadline column."""
    op.execute("""
        ALTER TABLE tasks 
        ALTER COLUMN deadline TYPE TIMESTAMP WITHOUT TIME ZONE
    """)

    op.execute("""
        ALTER TABLE tasks 
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
    """)

    op.execute("""
        ALTER TABLE tasks 
        ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE
    """)