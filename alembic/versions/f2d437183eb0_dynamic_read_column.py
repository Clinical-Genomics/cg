"""dynamic_read_column

Revision ID: f2d437183eb0
Revises: 97ffd22d7ebc
Create Date: 2023-06-27 14:13:45.653207

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2d437183eb0"
down_revision = "97ffd22d7ebc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sample", sa.Column("dynamic_read_count", sa.BigInteger, nullable=True))


def downgrade():
    op.drop_column("sample", "dynamic_read_count")
