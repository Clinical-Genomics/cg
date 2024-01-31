"""remove_uploaded_to_vogue_at

Revision ID: 584840c706a0
Revises: 27ec5c4c0380
Create Date: 2023-12-27 11:50:22.278213

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "584840c706a0"
down_revision = "27ec5c4c0380"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("analysis", "uploaded_to_vogue_at")


def downgrade():
    op.add_column("analysis", sa.Column("uploaded_to_vogue_at", sa.DateTime(), nullable=True))
