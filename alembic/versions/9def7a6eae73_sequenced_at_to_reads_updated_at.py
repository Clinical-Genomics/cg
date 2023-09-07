"""Sequenced at to reads updated at

Revision ID: 9def7a6eae73
Revises: 5cb3ce4c3e39
Create Date: 2023-09-04 15:26:12.607703

"""

from alembic import op
from sqlalchemy import types

# revision identifiers, used by Alembic.
revision = "9def7a6eae73"
down_revision = "5cb3ce4c3e39"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        schema="cg-stage",
        table_name="Sample",
        column_name="sequenced_at",
        new_column_name="reads_updated_at",
        existing_type=types.DateTime,
    )


def downgrade():
    op.alter_column(
        schema="cg-stage",
        table_name="Sample",
        column_name="reads_updated_at",
        new_column_name="sequenced_at",
        existing_type=types.DateTime,
    )
