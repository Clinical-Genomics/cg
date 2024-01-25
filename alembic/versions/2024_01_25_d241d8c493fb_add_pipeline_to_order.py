"""Add pipeline to order

Revision ID: d241d8c493fb
Revises: a6befebf1231
Create Date: 2024-01-25 16:18:35.740780

"""
import sqlalchemy as sa

from alembic import op
from cg.constants import Pipeline

# revision identifiers, used by Alembic.
revision = "d241d8c493fb"
down_revision = "a6befebf1231"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="order",
        column=sa.Column(
            "pipeline",
            sa.Enum(*tuple(Pipeline)),
        ),
    )


def downgrade():
    op.drop_column(
        table_name="order",
        column_name="pipeline",
    )
