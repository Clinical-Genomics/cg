"""New order workflows

Revision ID: 2a0ec08b0922
Revises: b614a52759c5
Create Date: 2024-04-05 10:57:03.010785

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2a0ec08b0922"
down_revision = "b614a52759c5"
branch_labels = None
depends_on = None

old_workflows = [
    "balsamic",
    "balsamic-pon",
    "balsamic-qc",
    "balsamic-umi",
    "demultiplex",
    "fastq",
    "fluffy",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "raredisease",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "sars-cov-2",
]

new_workflows = old_workflows + ["tomte"]


def upgrade():
    op.alter_column(
        table_name="order",
        column_name="workflow",
        existing_type=sa.Enum(*old_workflows),
        type_=sa.Enum(*new_workflows),
    )


def downgrade():
    op.alter_column(
        table_name="order",
        column_name="workflow",
        existing_type=sa.Enum(*new_workflows),
        type_=sa.Enum(*old_workflows),
    )
