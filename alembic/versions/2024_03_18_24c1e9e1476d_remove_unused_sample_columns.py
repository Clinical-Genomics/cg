"""Remove unused sample columns

Revision ID: 24c1e9e1476d
Revises: b2fcb2ada306
Create Date: 2024-03-18 14:59:13.832047

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "24c1e9e1476d"
down_revision = "b2fcb2ada306"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("sample", "sequence_start")
    op.drop_column("sample", "is_external")
    op.drop_column("sample", "invoiced_at")


def downgrade():
    op.add_column("sample", sa.Column("invoiced_at", mysql.DATETIME(), nullable=True))
    op.add_column("sample", sa.Column("is_external", mysql.BOOLEAN(), nullable=True))
    op.add_column("sample", sa.Column("sequence_start", mysql.DATETIME(), nullable=True))
