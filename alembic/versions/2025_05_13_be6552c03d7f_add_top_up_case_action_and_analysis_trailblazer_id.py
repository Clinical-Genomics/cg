"""add top-up case action

Revision ID: be6552c03d7f
Revises: 8e0b9e03054d
Create Date: 2025-05-13 15:25:24.572276

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "be6552c03d7f"
down_revision = "8e0b9e03054d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="analysis",
        column=sa.Column("trailblazer_id", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column(table_name="analysis", column_name="trailblazer_id")
