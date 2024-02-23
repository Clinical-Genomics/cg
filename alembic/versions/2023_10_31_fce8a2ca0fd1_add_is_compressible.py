"""Add is_compressible

Revision ID: fce8a2ca0fd1
Revises: 9073c61bc72b
Create Date: 2023-10-31 10:18:11.450637

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fce8a2ca0fd1"
down_revision = "9073c61bc72b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "family",
        sa.Column("is_compressible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )


def downgrade():
    op.drop_column("family", "is_compressible")
