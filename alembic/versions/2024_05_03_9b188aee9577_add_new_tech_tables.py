"""add_new_tech_tables

Revision ID: 9b188aee9577
Revises: 9cf71c905539
Create Date: 2024-05-03 15:28:55.342488

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

# revision identifiers, used by Alembic.
revision = "9b188aee9577"
down_revision = "9cf71c905539"
branch_labels = None
depends_on = None
Base = declarative_base()


def upgrade():
    op.create_table(
        "run_device",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
    )

    op.create_table(
        "run_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
    )

    op.create_table(
        "sample_run_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("run_metrics_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
    )


def downgrade():
    op.drop_table("run_device")
    op.drop_table("run_metrics")
    op.drop_table("sample_run_metrics")
