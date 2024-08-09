"""add nanopore flow cell

Revision ID: 4ae0174bd308
Revises: 951939f0f9b7
Create Date: 2024-06-03 12:42:13.463437

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4ae0174bd308"
down_revision = "951939f0f9b7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "oxford_nanopore_flow_cell",
        sa.Column(
            "id", sa.Integer(), sa.ForeignKey("run_device.id"), nullable=False, primary_key=True
        ),
    )


def downgrade():
    op.drop_table("oxford_nanopore_flow_cell")
