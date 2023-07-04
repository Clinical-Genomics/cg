"""Add metrics unique constraint

Revision ID: 97ffd22d7ebc
Revises: 367ed257e4ee
Create Date: 2023-06-27 09:41:01.028587

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "97ffd22d7ebc"
down_revision = "367ed257e4ee"
branch_labels = None
depends_on = None


def upgrade():
    # Add a unique constraint
    op.create_unique_constraint(
        "uix_flowcell_sample_lane",
        "sample_lane_sequencing_metrics",
        ["flow_cell_name", "sample_internal_id", "flow_cell_lane_number"],
    )


def downgrade():
    # Drop the unique constraint
    op.drop_constraint("uix_flowcell_sample_lane", "sample_lane_sequencing_metrics", type_="unique")
