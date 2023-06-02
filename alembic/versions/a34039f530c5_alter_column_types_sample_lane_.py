"""alter column types sample lane sequencing metrics

Revision ID: a34039f530c5
Revises: e6a3f1ad4b50
Create Date: 2023-06-02 11:31:13.063065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a34039f530c5"
down_revision = "e6a3f1ad4b50"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        nullable=False,
        type_=sa.String(length=32),
    )

    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        nullable=False,
        type_=sa.String(length=32),
    )


def downgrade():
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        nullable=False,
        type_=sa.VARCHAR(length=128),
    )

    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        nullable=False,
        type_=sa.VARCHAR(length=128),
    )
