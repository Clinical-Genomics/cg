"""Rename q30 metrics column

Revision ID: 5cb3ce4c3e39
Revises: 201b16c45366
Create Date: 2023-08-18 13:56:53.793003

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "5cb3ce4c3e39"
down_revision = "201b16c45366"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_base_fraction_passing_q30",
        new_column_name="sample_base_percentage_passing_q30",
        type_=sa.Numeric(6, 2),
    )


def downgrade():
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_base_percentage_passing_q30",
        new_column_name="sample_base_fraction_passing_q30",
        type_=sa.Numeric(6, 2),
    )
