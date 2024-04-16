"""Remove order date from case

Revision ID: 0278168054c8
Revises: ac5a804a9f47
Create Date: 2024-04-16 18:25:28.424724

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "0278168054c8"
down_revision = "ac5a804a9f47"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("case", "ordered_at")


def downgrade():
    op.add_column("case", sa.Column("ordered_at", mysql.DATETIME(), nullable=True))
