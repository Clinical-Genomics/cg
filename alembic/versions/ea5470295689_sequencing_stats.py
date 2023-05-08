"""Add sequencing-stats table

Revision ID: ea5470295689
Revises: 9008aa5065b4
Create Date: 2023-05-04 09:29:09.945895

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, types, orm, ForeignKey

# revision identifiers, used by Alembic.
revision = "ea5470295689"
down_revision = "9008aa5065b4"
branch_labels = None
depends_on = None

Base = declarative_base()


def upgrade():
    op.create_table(
        "sequencing_statistics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("flow_cell_name", sa.String(128), nullable=False),
        sa.Column("sample_internal_id", sa.String(128), nullable=False),
        sa.Column("lane", sa.Integer(), nullable=False),
        sa.Column("yield_in_megabases", sa.Integer(), nullable=False),
        sa.Column("read_counts", sa.Integer(), nullable=False),
        sa.Column("passed_filter_percent", sa.Numeric(10, 5), nullable=False),
        sa.Column("raw_clusters_per_lane_percent", sa.Numeric(10, 5), nullable=False),
        sa.Column("bases_with_q30_percent", sa.Numeric(10, 5), nullable=False),
        sa.Column("perfect_index_reads_percent", sa.Numeric(10, 5), nullable=False),
        sa.Column("lanes_mean_quality_score", sa.Numeric(10, 5), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("sequencing_statistics")
