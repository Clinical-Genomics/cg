"""2024_05_22_add_yield_columns

Revision ID: 18e3b2aba252
Revises: 5fd7e8758fb1
Create Date: 2024-05-22 14:01:15.197675

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "18e3b2aba252"
down_revision = "5fd7e8758fb1"
branch_labels = None
depends_on = None


def upgrade():
    # rename table IlluminaSampleRunMetrics to IlluminaSampleSequencingMetrics
    op.rename_table(
        old_table_name="illumina_sample_run_metrics",
        new_table_name="illumina_sample_sequencing_metrics",
    )
    # add column yield
    op.add_column(
        table_name="illumina_sample_sequencing_metrics",
        column=sa.Column("yield", sa.Integer(), nullable=True),
    )
    # add column yield_q30
    op.add_column(
        table_name="illumina_sample_sequencing_metrics",
        column=sa.Column("yield_q30", sa.Float(), nullable=True),
    )
    # rename  table run metrics to InstrumentRun
    op.rename_table(
        old_table_name="run_metrics",
        new_table_name="instrument_run",
    )
    # on SampleRunMetrics change run_metrics_id to instrument_run_id
    op.alter_column(
        table_name="sample_run_metrics",
        column_name="run_metrics_id",
        new_column_name="instrument_run_id",
        type_=sa.Integer(),
    )
    # rename illumina_sequencing_metrics to illumina_sequencing_run
    op.rename_table(
        old_table_name="illumina_sequencing_metrics",
        new_table_name="illumina_sequencing_run",
    )


def downgrade():
    # rename illumina_sequencing_metrics to illumina_sequencing_run
    op.rename_table(
        new_table_name="illumina_sequencing_metrics",
        old_table_name="illumina_sequencing_run",
    )

    # on SampleRunMetrics change run_metrics_id to instrument_run_id
    op.alter_column(
        table_name="sample_run_metrics",
        new_column_name="run_metrics_id",
        column_name="instrument_run_id",
        type_=sa.Integer(),
    )
    # rename run metrics -> InstrumentRun
    op.rename_table(
        new_table_name="run_metrics",
        old_table_name="instrument_run",
    )

    # drop columns yield and yield_q30
    op.drop_column(table_name="illumina_sample_sequencing_metrics", column_name="yield")
    op.drop_column(table_name="illumina_sample_sequencing_metrics", column_name="yield_q30")

    # rename table IlluminaSampleSequencingMetrics to IlluminaSampleRunMetrics
    op.rename_table(
        new_table_name="illumina_sample_run_metrics",
        old_table_name="illumina_sample_sequencing_metrics",
    )
