"""Add foreign keys to SampleLaneSequencingMetrics

Revision ID: 9d1483e638af
Revises: f5e0db62a5a7
Create Date: 2023-06-01 13:40:25.835471

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "9d1483e638af"
down_revision = "f5e0db62a5a7"
branch_labels = None
depends_on = None


def upgrade():
    # Add foreign key constraints to SampleLaneSequencingMetrics table
    op.add_column(
        "sample_lane_sequencing_metrics",
        sa.Column("flow_cell_name", sa.String(length=128), nullable=False),
    )
    op.create_foreign_key(
        None, "sample_lane_sequencing_metrics", "flowcell", ["flow_cell_name"], ["name"]
    )
    op.add_column(
        "sample_lane_sequencing_metrics",
        sa.Column("sample_internal_id", sa.String(length=128), nullable=False),
    )
    op.create_foreign_key(
        None, "sample_lane_sequencing_metrics", "sample", ["sample_internal_id"], ["internal_id"]
    )

    # Add relationships to Flowcell and Sample models
    op.add_column(
        "flowcell", sa.Column("sample_lane_sequencing_metrics_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        None,
        "flowcell",
        "sample_lane_sequencing_metrics",
        ["sample_lane_sequencing_metrics_id"],
        ["id"],
    )
    op.create_index(None, "flowcell", ["sample_lane_sequencing_metrics_id"], unique=False)
    op.add_column(
        "sample", sa.Column("sample_lane_sequencing_metrics_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        None,
        "sample",
        "sample_lane_sequencing_metrics",
        ["sample_lane_sequencing_metrics_id"],
        ["id"],
    )
    op.create_index(None, "sample", ["sample_lane_sequencing_metrics_id"], unique=False)


def downgrade():
    # Remove relationships from Flowcell and Sample models
    op.drop_constraint(None, "sample", type_="foreignkey")
    op.drop_column("sample", "sample_lane_sequencing_metrics_id")
    op.drop_index(None, "sample", ["sample_lane_sequencing_metrics_id"])
    op.drop_constraint(None, "flowcell", type_="foreignkey")
    op.drop_column("flowcell", "sample_lane_sequencing_metrics_id")
    op.drop_index(None, "flowcell", ["sample_lane_sequencing_metrics_id"])

    # Remove foreign key constraints from SampleLaneSequencingMetrics table
    op.drop_constraint(None, "sample_lane_sequencing_metrics", type_="foreignkey")
    op.drop_column("sample_lane_sequencing_metrics", "flow_cell_name")
    op.drop_constraint(None, "sample_lane_sequencing_metrics", type_="foreignkey")
    op.drop_column("sample_lane_sequencing_metrics", "sample_internal_id")
