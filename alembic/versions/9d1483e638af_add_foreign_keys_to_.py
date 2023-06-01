"""Add foreign keys to SampleLaneSequencingMetrics

Revision ID: 9d1483e638af
Revises: f5e0db62a5a7
Create Date: 2023-06-01 13:40:25.835471

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9d1483e638af"
down_revision = "f5e0db62a5a7"
branch_labels = None
depends_on = None


def upgrade():
    # Add foreign key constraints to SampleLaneSequencingMetrics table
    op.create_foreign_key(
        None, "sample_lane_sequencing_metrics", "flowcell", ["flow_cell_name"], ["name"]
    )
    op.create_foreign_key(
        None, "sample_lane_sequencing_metrics", "sample", ["sample_internal_id"], ["internal_id"]
    )


def downgrade():
    # Remove foreign key constraints from SampleLaneSequencingMetrics table
    op.drop_constraint(
        "sample_lane_sequencing_metrics_flow_cell_name_fkey",
        "sample_lane_sequencing_metrics",
        type_="foreignkey",
    )
    op.drop_constraint(
        "sample_lane_sequencing_metrics_sample_internal_id_fkey",
        "sample_lane_sequencing_metrics",
        type_="foreignkey",
    )