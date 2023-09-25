"""Sync the remaining parts of cg and statusdb

Revision ID: d0aa961845b9
Revises: 936887038ba8
Create Date: 2023-09-19 11:31:00.876262

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "d0aa961845b9"
down_revision = "936887038ba8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key("sample_invoice_ibfk_1", "sample", "invoice", ["invoice_id"], ["id"])
    op.drop_column("sample", "beaconized_at")
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=False,
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "sample_internal_id",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=True,
    )
    op.alter_column(
        "sample_lane_sequencing_metrics",
        "flow_cell_name",
        existing_type=mysql.VARCHAR(charset="latin1", collation="latin1_swedish_ci", length=32),
        nullable=True,
    )
    op.add_column("sample", sa.Column("beaconized_at", mysql.TEXT(), nullable=True))
    op.drop_constraint(
        constraint_name="sample_invoice_ibfk_1", table_name="sample", type_="foreignkey"
    )
