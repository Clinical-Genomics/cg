"""add_illumina_sample_run_metrics

Revision ID: 5c6de08c4aca
Revises: e5c6bf847e25
Create Date: 2024-05-15 09:02:42.837904

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5c6de08c4aca"
down_revision = "e5c6bf847e25"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "illumina_sample_run_metrics",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("flow_cell_lane", sa.Integer(), nullable=False),
        sa.Column("reads_in_lane", sa.BigInteger(), nullable=False),
        sa.Column("base_passing_q30_percent", sa.Float(), nullable=False),
        sa.Column("base_mean_quality_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("illumina_sample_run_metrics")
