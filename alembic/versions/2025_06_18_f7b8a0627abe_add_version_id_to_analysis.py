"""add version id to analysis

Revision ID: f7b8a0627abe
Revises: be6552c03d7f
Create Date: 2025-06-18 13:18:38.508216

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f7b8a0627abe"
down_revision = "be6552c03d7f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="analysis",
        column=sa.Column("housekeeper_version_id", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column(table_name="analysis", column_name="housekeeper_version_id")
