"""add uploaded to vogue column to analysis

Revision ID: 49ded71bd1a1
Revises: 089edc289291
Create Date: 2021-03-10 13:32:40.247574

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "49ded71bd1a1"
down_revision = "089edc289291"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("analysis", sa.Column("uploaded_to_vogue_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("analysis", "uploaded_to_vogue_at")
