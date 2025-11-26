"""add session_id to analysis

Revision ID: 3874118753ff
Revises: 2d63ba0d1154
Create Date: 2025-11-18 10:36:08.049049

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3874118753ff"
down_revision = "2d63ba0d1154"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="analysis", column=sa.Column("session_id", sa.String(length=128), nullable=True)
    )


def downgrade():
    op.drop_column(table_name="analysis", column_name="session_id")
