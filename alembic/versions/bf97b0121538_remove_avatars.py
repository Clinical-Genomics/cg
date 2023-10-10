"""remove avatars

Revision ID: bf97b0121538
Revises: 76e8252a6efb
Create Date: 2022-02-25 16:13:16.666812

"""
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from alembic import op

# revision identifiers, used by Alembic.
revision = "bf97b0121538"
down_revision = "76e8252a6efb"
branch_labels = None
depends_on = None

Base = declarative_base()


def upgrade():
    op.drop_column("family", "avatar_url")


def downgrade():
    op.add_column("family", sa.Column("avatar_url", sa.TEXT))
