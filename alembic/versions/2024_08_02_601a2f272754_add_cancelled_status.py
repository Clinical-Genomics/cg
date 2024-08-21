"""Add cancelled status

Revision ID: 601a2f272754
Revises: 0ca61967d364
Create Date: 2024-08-02 11:59:42.391980

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "601a2f272754"
down_revision = "0ca61967d364"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="sample",
        column=sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column(table_name="sample", column_name="is_cancelled")
