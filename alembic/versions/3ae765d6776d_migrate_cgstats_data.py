"""Migration of data in the cgstats unaligned database table into the cg SampleLaneSequencingMetrics table.

Revision ID: 3ae765d6776d
Revises: 367ed257e4ee
Create Date: 2023-06-22 15:18:18.623714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3ae765d6776d"
down_revision = "367ed257e4ee"
branch_labels = None
depends_on = None


def upgrade():
    # Execute the query and insert data into the existing table
    op.execute(
        """
        INSERT INTO sample_statistics (
            sample_internal_id,
            flow_cell_name,
            flow_cell_lane_number,
            sample_total_reads_in_lane,
            sample_base_fraction_passing_q30,
            sample_base_mean_quality_score,
            created_at
        )
        SELECT
            cgstats.sample.limsid AS sample_internal_id,
            cgstats.flowcell.flowcellname AS flow_cell_name,
            cgstats.unaligned.lane AS flow_cell_lane_number,
            cgstats.unaligned.readcounts AS sample_total_reads_in_lane,
            cgstats.unaligned.q30_bases_pct AS sample_base_fraction_passing_q30,
            cgstats.unaligned.mean_quality_score AS sample_base_mean_quality_score,
            cgstats.unaligned.time AS created_at
        FROM
            cgstats.sample
            JOIN cg.sample ON cgstats.sample.limsid = cg.sample.internal_id
            JOIN cgstats.unaligned ON cgstats.sample.sample_id = cgstats.unaligned.sample_id
            JOIN cgstats.demux ON cgstats.unaligned.demux_id = cgstats.demux.demux_id
            JOIN cgstats.flowcell ON cgstats.demux.flowcell_id = cgstats.flowcell.flowcell_id
        """
    )


def downgrade():
    # Implement the necessary steps to downgrade the migration if needed
    pass
