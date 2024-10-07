"""Refactor pacbio models

Revision ID: d6474325c722
Revises: 18dbadd8c436
Create Date: 2024-09-27 15:40:49.040271

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "d6474325c722"
down_revision = "18dbadd8c436"
branch_labels = None
depends_on = None


def upgrade():
    # PacbioSequencingRun
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_reads", sa.BIGINT, nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_reads_percentage", sa.FLOAT, nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_yield", sa.BIGINT, nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_yield_percentage", sa.FLOAT, nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_mean_read_length", sa.BIGINT, nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("run_name", type_=mysql.VARCHAR(64), nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("unbarcoded_hifi_reads", sa.BIGINT, nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("unbarcoded_hifi_yield", sa.BIGINT, nullable=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("unbarcoded_hifi_mean_read_length", sa.BIGINT, nullable=True),
    )

    # PacbioSampleSequencingMetrics
    op.add_column(
        table_name="pacbio_sample_run_metrics",
        column=sa.Column("polymerase_mean_read_length", sa.BIGINT, nullable=True),
    )
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="percent_reads_passing_q30")
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="failed_reads")
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="failed_yield")
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="failed_mean_read_length")


def downgrade():
    # PacbioSequencingRun
    op.drop_column(table_name="pacbio_sequencing_run", column_name="barcoded_hifi_reads")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="barcoded_hifi_reads_percentage")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="barcoded_hifi_yield")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="barcoded_hifi_yield_percentage")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="barcoded_hifi_mean_read_length")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="run_name")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="unbarcoded_hifi_reads")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="unbarcoded_hifi_yield")
    op.drop_column(
        table_name="pacbio_sequencing_run", column_name="unbarcoded_hifi_mean_read_length"
    )

    # PacbioSampleSequencingMetrics
    op.drop_column(
        table_name="pacbio_sample_run_metrics", column_name="polymerase_mean_read_length"
    )
    op.add_column(
        table_name="pacbio_sample_run_metrics",
        column=sa.Column("percent_reads_passing_q30", sa.FLOAT, nullable=False),
    )
    op.add_column(
        table_name="pacbio_sample_run_metrics",
        column=sa.Column("failed_reads", sa.BIGINT, nullable=False),
    )
    op.add_column(
        table_name="pacbio_sample_run_metrics",
        column=sa.Column("failed_yield", sa.BIGINT, nullable=False),
    )
    op.add_column(
        table_name="pacbio_sample_run_metrics",
        column=sa.Column("failed_mean_read_length", sa.BIGINT, nullable=False),
    )
