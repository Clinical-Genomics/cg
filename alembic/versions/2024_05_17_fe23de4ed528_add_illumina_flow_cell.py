"""add_illumina_flow_cell

Revision ID: fe23de4ed528
Revises: 6e6c36d5157b
Create Date: 2024-05-17 15:09:12.088324

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "fe23de4ed528"
down_revision = "6e6c36d5157b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "illumina_flow_cell",
        sa.Column(
            "id", sa.Integer(), sa.ForeignKey("run_device.id"), nullable=False, primary_key=True
        ),
        sa.Column("model", sa.String(length=32), nullable=False),
    )


def downgrade():
    op.drop_table("illumina_flow_cell")
