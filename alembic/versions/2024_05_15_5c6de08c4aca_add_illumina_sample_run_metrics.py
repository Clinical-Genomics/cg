"""add_illumina_sample_run_metrics

Revision ID: 5c6de08c4aca
Revises: fa7a3d066872
Create Date: 2024-05-15 09:02:42.837904

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5c6de08c4aca"
down_revision = "fa7a3d066872"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "illumina_sample_run_metrics",
        sa.Column("id", sa.Integer(), sa.ForeignKey("sample_run_metrics.id"), primary_key=True),
        sa.Column("flow_cell_lane", sa.Integer(), nullable=True),
        sa.Column("total_reads_in_lane", sa.BigInteger(), nullable=True),
        sa.Column("base_passing_q30_percent", sa.Numeric(6, 2), nullable=True),
        sa.Column("base_mean_quality_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("illumina_sample_run_metrics")
