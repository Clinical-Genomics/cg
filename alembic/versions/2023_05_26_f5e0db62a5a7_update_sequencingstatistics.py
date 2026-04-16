"""Transform SequencingStatistics to SampleLaneSequencingMetrics

Revision ID: f5e0db62a5a7
Revises: ea5470295689
Create Date: 2023-05-26 09:56:45.431450

"""

import sqlalchemy as sa

from alembic import op

revision = "f5e0db62a5a7"
down_revision = "ea5470295689"
branch_labels = None
depends_on = None


def upgrade():
    # create new table
    op.create_table(
        "sample_lane_sequencing_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("flow_cell_name", sa.String(128), nullable=False),
        sa.Column("flow_cell_lane_number", sa.Integer),
        sa.Column("sample_internal_id", sa.String(128), nullable=False),
        sa.Column("sample_total_reads_in_lane", sa.Integer),
        sa.Column("sample_base_fraction_passing_q30", sa.Numeric(10, 5)),
        sa.Column("sample_base_mean_quality_score", sa.Numeric(10, 5)),
        sa.Column("created_at", sa.DateTime),
    )

    # migrate data from old table to new one
    op.execute("""
        INSERT INTO sample_lane_sequencing_metrics (id, flow_cell_name, flow_cell_lane_number, 
        sample_internal_id, sample_total_reads_in_lane, sample_base_fraction_passing_q30, 
        sample_base_mean_quality_score, created_at)
        SELECT id, flow_cell_name, lane as flow_cell_lane_number, sample_internal_id, read_counts as sample_total_reads_in_lane, 
        bases_with_q30_percent as sample_base_fraction_passing_q30, lanes_mean_quality_score as sample_base_mean_quality_score, 
        started_at as created_at
        FROM sequencing_statistics
    """)

    # drop old table
    op.drop_table("sequencing_statistics")


def downgrade():
    # Recreate the original SequencingStatistics table
    op.create_table(
        "sequencing_statistics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("flow_cell_name", sa.String(128), nullable=False),
        sa.Column("sample_internal_id", sa.String(128), nullable=False),
        sa.Column("lane", sa.Integer),
        sa.Column("yield_in_megabases", sa.Integer),
        sa.Column("read_counts", sa.Integer),
        sa.Column("passed_filter_percent", sa.Numeric(10, 5)),
        sa.Column("raw_clusters_per_lane_percent", sa.Numeric(10, 5)),
        sa.Column("perfect_index_reads_percent", sa.Numeric(10, 5)),
        sa.Column("bases_with_q30_percent", sa.Numeric(10, 5)),
        sa.Column("lanes_mean_quality_score", sa.Numeric(10, 5)),
        sa.Column("started_at", sa.DateTime),
    )

    # Migrate data back to old table
    op.execute("""
        INSERT INTO sequencing_statistics (id, flow_cell_name, lane, sample_internal_id, read_counts, 
        bases_with_q30_percent, lanes_mean_quality_score, started_at)
        SELECT id, flow_cell_name, flow_cell_lane_number as lane, sample_internal_id, 
        sample_total_reads_in_lane as read_counts, sample_base_fraction_passing_q30 as bases_with_q30_percent, 
        sample_base_mean_quality_score as lanes_mean_quality_score, created_at as started_at
        FROM sample_lane_sequencing_metrics
    """)

    # drop the new table
    op.drop_table("sample_lane_sequencing_metrics")
