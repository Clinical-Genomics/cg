"""Remove order date from pool

Revision ID: dd3fd72df1ae
Revises: ac5a804a9f47
Create Date: 2024-04-16 18:51:33.598555

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "dd3fd72df1ae"
down_revision = "ac5a804a9f47"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("pool", "ordered_at")


def downgrade():
    op.add_column("pool", sa.Column("ordered_at", mysql.DATETIME(), nullable=False))
