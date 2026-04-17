"""make case created at non nullable

Revision ID: 15d1eece1f2b
Revises: 96667267134e
Create Date: 2026-04-17 15:57:28.767193

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "15d1eece1f2b"
down_revision = "96667267134e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="case",
        column_name="created_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        table_name="case",
        column_name="created_at",
        existing_type=sa.DateTime(),
        nullable=True,
    )
