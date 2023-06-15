"""Add index to sequencing metrics sample id

Revision ID: 879e6bc89750
Revises: 367ed257e4ee
Create Date: 2023-06-14 18:09:03.849372

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "879e6bc89750"
down_revision = "367ed257e4ee"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_sample_internal_id",
        "sample_lane_sequencing_metrics",
        ["sample_internal_id"],
    )


def downgrade():
    op.drop_index("idx_sample_internal_id", table_name="sample_lane_sequencing_metrics")
