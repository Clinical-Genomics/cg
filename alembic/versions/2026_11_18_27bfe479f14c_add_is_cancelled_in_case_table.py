"""add_is_cancelled_in_case_table

Revision ID: 27bfe479f14c
Revises: 203421044513
Create Date: 2026-11-18 18:33:00.907021

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "27bfe479f14c"
down_revision = "203421044513"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="case",
        column=sa.Column(
            name="is_cancelled",
            type_=sa.Boolean,
            nullable=False,
            default=False,
        ),
    )


def downgrade():
    op.drop_column(table_name="case", column_name="is_cancelled")
