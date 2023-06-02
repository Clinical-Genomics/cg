"""Change data type of metrics

Revision ID: 367ed257e4ee
Revises: 869d352cc614
Create Date: 2023-06-02 16:10:19.975435

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "367ed257e4ee"
down_revision = "869d352cc614"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_base_fraction_passing_q30",
        type_=sa.Numeric(precision=5, scale=2),
        existing_type=sa.Numeric(precision=10, scale=5),
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_base_mean_quality_score",
        type_=sa.Numeric(precision=5, scale=2),
        existing_type=sa.Numeric(precision=10, scale=5),
    )


def downgrade():
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_base_mean_quality_score",
        type_=sa.Numeric(precision=10, scale=5),
        existing_type=sa.Numeric(precision=5, scale=2),
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_base_fraction_passing_q30",
        type_=sa.Numeric(precision=10, scale=5),
        existing_type=sa.Numeric(precision=5, scale=2),
    )
