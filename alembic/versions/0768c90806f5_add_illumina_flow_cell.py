"""add_illumina_flow_cell

Revision ID: 0768c90806f5
Revises: 5c6de08c4aca
Create Date: 2024-05-16 16:07:05.877295

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0768c90806f5"
down_revision = "5c6de08c4aca"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "illumina_flow_cell",
        sa.Column("id", sa.ForeignKey("run_device.id"), nullable=False, primary_key=True),
    )


def downgrade():
    op.drop_table("illumina_flow_cell")
