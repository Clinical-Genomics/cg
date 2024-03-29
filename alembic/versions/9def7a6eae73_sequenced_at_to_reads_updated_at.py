"""Sequenced at to reads updated at

Revision ID: 9def7a6eae73
Revises: c3da223e60d8
Create Date: 2023-09-04 15:26:12.607703

"""

from sqlalchemy import types

from alembic import op

# revision identifiers, used by Alembic.
revision = "9def7a6eae73"
down_revision = "c3da223e60d8"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="sample",
        column_name="sequenced_at",
        new_column_name="reads_updated_at",
        existing_type=types.DateTime,
    )


def downgrade():
    op.alter_column(
        table_name="sample",
        column_name="reads_updated_at",
        new_column_name="sequenced_at",
        existing_type=types.DateTime,
    )
