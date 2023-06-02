"""Add relationship between metrics and flowcell

Revision ID: 869d352cc614
Revises: a34039f530c5
Create Date: 2023-06-02 12:55:31.520397

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.types import VARCHAR

# revision identifiers, used by Alembic.
revision = "869d352cc614"
down_revision = "a34039f530c5"
branch_labels = None
depends_on = None


def upgrade():
    # Add foreign key constraint to flow_cell_name column in SampleLaneSequencingMetrics
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        type_=VARCHAR(32, collation="latin1_swedish_ci"),
    )
    op.create_foreign_key(
        "fk_sample_lane_sequencing_metrics_flowcell",
        "sample_lane_sequencing_metrics",
        "flowcell",
        ["flow_cell_name"],
        ["name"],
    )

    # Add foreign key constraint to sample_internal_id column in SampleLaneSequencingMetrics
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        type_=VARCHAR(32, collation="latin1_swedish_ci"),
    )
    op.create_foreign_key(
        "fk_sample_lane_sequencing_metrics_sample",
        "sample_lane_sequencing_metrics",
        "sample",
        ["sample_internal_id"],
        ["internal_id"],
    )


def downgrade():
    # Remove foreign key constraint from flow_cell_name column in SampleLaneSequencingMetrics
    op.drop_constraint(
        "fk_sample_lane_sequencing_metrics_flowcell",
        "sample_lane_sequencing_metrics",
        type_="foreignkey",
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        type_=VARCHAR(32, collation="utf8mb4_0900_ai_ci"),
    )

    # Remove foreign key constraint from sample_internal_id column in SampleLaneSequencingMetrics
    op.drop_constraint(
        "fk_sample_lane_sequencing_metrics_sample",
        "sample_lane_sequencing_metrics",
        type_="foreignkey",
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        type_=VARCHAR(32, collation="utf8mb4_0900_ai_ci"),
    )