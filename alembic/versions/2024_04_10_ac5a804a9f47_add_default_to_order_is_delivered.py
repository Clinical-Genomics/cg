"""Add default to order is_delivered

Revision ID: ac5a804a9f47
Revises: 0395f682958e
Create Date: 2024-04-10 12:40:31.208716

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "ac5a804a9f47"
down_revision = "0395f682958e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("order", "is_delivered", server_default=sa.false())


def downgrade():
    op.alter_column("order", "is_delivered", server_default=None)
