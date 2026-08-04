"""Drop unused tables

Revision ID: d2900fdde3e8
Revises: 018439b02e2e
Create Date: 2026-08-04 13:48:47.879475

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "d2900fdde3e8"
down_revision = "018439b02e2e"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table(table_name="sample_lane_sequencing_metrics")
    op.drop_table(table_name="flowcell")
    op.drop_table(table_name="flowcell_sample")
    op.drop_table(table_name="sample_info")


def downgrade():
    op.create_table(
        "sample_info",
        sa.Column(
            "internal_id",
            mysql.VARCHAR(32, collation="latin1_swedish_ci"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "name",
            mysql.VARCHAR(128, collation="latin1_swedish_ci"),
            nullable=False,
        ),
        sa.Column(
            "order",
            mysql.VARCHAR(64, collation="latin1_swedish_ci"),
            nullable=True,
        ),
        sa.Column(
            "original_ticket",
            mysql.VARCHAR(32, collation="latin1_swedish_ci"),
            nullable=True,
        ),
        sa.Column("reads", sa.BigInteger(), nullable=True),
        sa.Column("ordered_at", sa.DateTime(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("prepared_at", sa.DateTime(), nullable=True),
        sa.Column("last_sequenced_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("application_version_id", sa.Integer(), nullable=False),
        sa.Column(
            "priority",
            mysql.ENUM(
                "research",
                "standard",
                "priority",
                "express",
                "clinical_trials",
            ),
            nullable=False,
        ),
    )

    op.create_table(
        "flowcell_sample",
        sa.Column(
            sa.ForeignKey("flowcell.id", name="flowcell_sample_ibfk_1"),
            name="flowcell_id",
            type_=sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            sa.ForeignKey("sample.id", name="flowcell_sample_ibfk_2"),
            name="sample_id",
            type_=sa.Integer(),
            index=True,
            nullable=False,
        ),
        sa.UniqueConstraint("flowcell_id", "sample_id", name="_flowcell_sample_uc"),
    )

    op.create_table(
        "flowcell",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
        sa.Column("name", sa.String(32), unique=True, nullable=False),
        sa.Column(
            "sequencer_type",
            sa.Enum(
                "hiseqga",
                "hiseqx",
                "novaseq",
                "novaseqx",
                name="sequencer_type",
            ),
            nullable=True,
        ),
        sa.Column("sequencer_name", sa.String(32), nullable=True),
        sa.Column("sequenced_at", sa.DateTime(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "ondisk",
                "removed",
                "requested",
                "processing",
                "retrieved",
                name="flowcell_status",
            ),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("has_backup", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "sample_lane_sequencing_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
        sa.Column(
            sa.ForeignKey("flowcell.name", name="fk_sample_lane_sequencing_metrics_flowcell"),
            name="flow_cell_name",
            type_=mysql.VARCHAR(32, collation="latin1_swedish_ci"),
            nullable=False,
        ),
        sa.Column("flow_cell_lane_number", sa.Integer(), nullable=True),
        sa.Column(
            sa.ForeignKey("sample.internal_id", name="fk_sample_lane_sequencing_metrics_sample"),
            name="sample_internal_id",
            type_=mysql.VARCHAR(32, collation="latin1_swedish_ci"),
            index=True,
            nullable=False,
        ),
        sa.Column("sample_total_reads_in_lane", sa.BigInteger(), nullable=True),
        sa.Column(
            "sample_base_percentage_passing_q30",
            sa.DECIMAL(6, 2),
            nullable=True,
        ),
        sa.Column(
            "sample_base_mean_quality_score",
            sa.DECIMAL(6, 2),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "flow_cell_name",
            "sample_internal_id",
            "flow_cell_lane_number",
            name="uix_flowcell_sample_lane",
        ),
    )
