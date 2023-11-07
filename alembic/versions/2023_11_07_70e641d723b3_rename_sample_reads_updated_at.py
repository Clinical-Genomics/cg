"""Rename sample reads_updated_at

Revision ID: 70e641d723b3
Revises: fce8a2ca0fd1
Create Date: 2023-11-07 10:05:05.324260

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "70e641d723b3"
down_revision = "fce8a2ca0fd1"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "sample",
        "reads_updated_at",
        new_column_name="last_sequenced_at",
        existing_type=sa.DateTime(),
    )


def downgrade():
    op.alter_column(
        "sample",
        "last_sequenced_at",
        new_column_name="reads_updated_at",
        existing_type=sa.DateTime(),
    )
