"""Refactor pacbio models

Revision ID: d6474325c722
Revises: 18dbadd8c436
Create Date: 2024-09-27 15:40:49.040271

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d6474325c722"
down_revision = "18dbadd8c436"
branch_labels = None
depends_on = None


def upgrade():
    # PacBioSequencingRun
    op.add_column(
        table_name="pacbio_sequencing_run", column=sa.Column("barcoded_hifi_reads", sa.INTEGER)
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_reads_percentage", sa.FLOAT),
    )
    op.add_column(
        table_name="pacbio_sequencing_run", column=sa.Column("barcoded_hifi_yield", sa.INTEGER)
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_yield_percentage", sa.FLOAT),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("barcoded_hifi_mean_read_length", sa.INTEGER),
    )
    op.add_column(
        table_name="pacbio_sequencing_run", column=sa.Column("unbarcoded_hifi_reads", sa.INTEGER)
    )
    op.add_column(
        table_name="pacbio_sequencing_run", column=sa.Column("unbarcoded_hifi_yield", sa.INTEGER)
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("unbarcoded_hifi_mean_read_length", sa.INTEGER),
    )

    # PacBioSampleSequencingMetrics
    op.add_column(
        table_name="pacbio_sample_run_metrics",
        column=sa.Column("polymerase_mean_read_length", sa.INTEGER),
    )
    op.add_column(
        table_name="pacbio_sample_run_metrics", column=sa.Column("barcode", sa.VARCHAR(length=32))
    )
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="percent_reads_passing_q30")
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="failed_reads")
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="failed_yield")
    op.drop_column(table_name="pacbio_sample_run_metrics", column_name="failed_mean_read_length")


def downgrade():
    pass
