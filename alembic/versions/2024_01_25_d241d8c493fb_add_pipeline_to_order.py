"""Add pipeline to order

Revision ID: d241d8c493fb
Revises: de0f5b78dca4
Create Date: 2024-01-25 16:18:35.740780

"""

import sqlalchemy as sa

from alembic import op
from cg.constants import Workflow

# revision identifiers, used by Alembic.
revision = "d241d8c493fb"
down_revision = "de0f5b78dca4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="order",
        column=sa.Column("workflow", sa.Enum(*tuple(Workflow)), nullable=False),
    )


def downgrade():
    op.drop_column(
        table_name="order",
        column_name="workflow",
    )
