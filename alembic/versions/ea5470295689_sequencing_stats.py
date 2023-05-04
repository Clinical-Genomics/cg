"""Add sequencing-stats table

Revision ID: ea5470295689
Revises: 9008aa5065b4
Create Date: 2023-05-04 09:29:09.945895

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.
revision = "ea5470295689"
down_revision = "9008aa5065b4"
branch_labels = None
depends_on = None

Base = declarative_base()


def upgrade():
    op.create_table(
        "sequencing_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sample_internal_id"], ["sample.internal_id"]),
        sa.ForeignKeyConstraint(
            ["flow_cell_name"],
            ["flowcell.name"],
        ),
        sa.Column("lane", sa.Integer(), nullable=False),
        sa.Column("yield_mb", sa.Integer(), nullable=False),
        sa.Column("read_counts", sa.Integer(), nullable=False),
        sa.Column("raw_clusters_per_lane_pct", sa.Numeric(10, 5), nullable=False),
        sa.Column("q30_bases_pct", sa.Numeric(10, 5), nullable=False),
        sa.Column("passed_filter_pct", sa.Numeric(10, 5), nullable=False),
        sa.Column("mean_quality_score", sa.Numeric(10, 5), nullable=False),
        sa.Column("perfect_index_reads_pct", sa.Numeric(10, 5), nullable=False),
    )


def downgrade():
    op.drop_table("customer_user")
