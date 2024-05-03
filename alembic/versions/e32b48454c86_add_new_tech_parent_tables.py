"""Add new tech parent tables

Revision ID: e32b48454c86
Revises: 0fda0f2746d6
Create Date: 2024-05-03 14:33:20.886824

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

# revision identifiers, used by Alembic.
revision = "e32b48454c86"
down_revision = "0fda0f2746d6"
branch_labels = None
depends_on = None

Base = declarative_base()


def upgrade():
    op.create_table(
        "run_device",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(128), nullable=False),
        sa.Column("device_id", sa.String(128), nullable=False),
    )

    op.create_table(
        "run_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(128), nullable=False),
    )

    op.create_table(
        "sample_run_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sample_id", sa.Integer(), nullable=False),
        sa.Column("run_metrics_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(128), nullable=False),
    )


def downgrade():
    op.drop_table("run_device")
    op.drop_table("run_metrics")
    op.drop_table("sample_run_metrics")
