"""Set workflow and data delivery as mandatory

Revision ID: 11c84d89f2c1
Revises: 203421044513
Create Date: 2026-11-27 15:22:55.346254

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "11c84d89f2c1"
down_revision = "203421044513"
branch_labels = None
depends_on = None

WORKFLOWS = [
    "balsamic",
    "balsamic-pon",
    "balsamic-umi",
    "demultiplex",
    "fluffy",
    "jasen",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "nallo",
    "oncoflow",
    "raredisease",
    "raw-data",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
    "trana",
]


def upgrade():
    op.alter_column(
        table_name="analysis",
        column_name="workflow",
        nullable=False,
        existing_type=sa.Enum(*WORKFLOWS),
    )
    op.alter_column(
        table_name="case", column_name="data_delivery", nullable=False, existing_type=sa.VARCHAR(64)
    )


def downgrade():
    op.alter_column(
        table_name="case",
        column_name="data_delivery",
        nullable=True,
        existing_type=sa.VARCHAR(64),
    )
    op.alter_column(
        table_name="analysis",
        column_name="workflow",
        nullable=True,
        existing_type=sa.Enum(*WORKFLOWS),
    )
