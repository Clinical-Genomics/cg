"""add data archive location

Revision ID: c3fdf3a8a5b3
Revises: ffb9f8ab8e62
Create Date: 2023-07-04 15:29:48.507215

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3fdf3a8a5b3"
down_revision = "ffb9f8ab8e62"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="customer", column=sa.column("data_archive_location", sa.String(length=32))
    )


def downgrade():
    op.drop_column(table_name="customer", column_name="data_archive_location")
