"""Add delivery date to order

Revision ID: 752e8f0ce514
Revises: ac5a804a9f47
Create Date: 2024-04-17 09:57:39.761592

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "752e8f0ce514"
down_revision = "ac5a804a9f47"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("order", sa.Column("delivered_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("order", "delivered_at")
