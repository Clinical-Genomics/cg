"""add_illumina_run_metrics

Revision ID: 6e6c36d5157b
Revises: 5c6de08c4aca
Create Date: 2024-05-16 13:40:36.754552

"""

from enum import StrEnum

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6e6c36d5157b"
down_revision = "5c6de08c4aca"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "illumina_sequencing_metrics",
        sa.Column(
            "id", sa.Integer(), sa.ForeignKey("run_metrics.id"), nullable=False, primary_key=True
        ),
        sa.Column("sequencer_type", sa.String(length=32), nullable=True),
        sa.Column("sequencer_name", sa.String(length=32), nullable=True),
        sa.Column("sequenced_at", sa.DateTime(), nullable=True),
        sa.Column("data_availability", sa.String(length=32), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("has_backup", sa.Boolean(), nullable=False),
        sa.Column("total_reads", sa.BigInteger(), nullable=True),
        sa.Column("total_undetermined_reads", sa.BigInteger(), nullable=True),
        sa.Column("percent_q30", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("mean_quality_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("total_yield", sa.BigInteger(), nullable=True),
        sa.Column("yield_q30", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("cycles", sa.Integer(), nullable=True),
        sa.Column("demultiplexing_software", sa.String(length=32), nullable=True),
        sa.Column("demultiplexing_software_version", sa.String(length=32), nullable=True),
        sa.Column("sequencing_started_at", sa.DateTime(), nullable=True),
        sa.Column("sequencing_completed_at", sa.DateTime(), nullable=True),
        sa.Column("demultiplexing_started_at", sa.DateTime(), nullable=True),
        sa.Column("demultiplexing_completed_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("illumina_run_metrics")
