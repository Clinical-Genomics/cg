"""Make short name non-nullable

Revision ID: 2d63ba0d1154
Revises: e0a3e31ed84e
Create Date: 2025-10-23 14:24:48.182207

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "2d63ba0d1154"
down_revision = "e0a3e31ed84e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="bed_version",
        column_name="shortname",
        existing_type=mysql.VARCHAR(length=64),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        table_name="bed_version",
        column_name="shortname",
        existing_type=mysql.VARCHAR(length=64),
        nullable=True,
    )
