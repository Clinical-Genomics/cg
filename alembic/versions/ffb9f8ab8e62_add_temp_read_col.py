"""add_temp_read_col

Revision ID: ffb9f8ab8e62
Revises: 97ffd22d7ebc
Create Date: 2023-06-29 08:39:28.254889

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ffb9f8ab8e62"
down_revision = "97ffd22d7ebc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="sample", column=sa.Column("calculated_read_count", sa.BigInteger(), default=0)
    )


def downgrade():
    op.drop_column(table_name="sample", column_name="calculated_read_count")
