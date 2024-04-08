"""Add order delivery

Revision ID: 0395f682958e
Revises: b614a52759c5
Create Date: 2024-04-08 16:35:41.629048

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0395f682958e"
down_revision = "b614a52759c5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("order", sa.Column("delivered", sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column("order", "delivered")
