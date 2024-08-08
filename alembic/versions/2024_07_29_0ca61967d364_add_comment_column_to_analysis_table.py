"""Add comment column to analysis table

Revision ID: 0ca61967d364
Revises: 77a75121be31
Create Date: 2024-07-29 10:43:06.444590

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0ca61967d364"
down_revision = "77a75121be31"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="analysis",
        column=sa.Column("comment", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column(table_name="analysis", column_name="comment")
