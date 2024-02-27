"""Add pipeline to order

Revision ID: d241d8c493fb
Revises: de0f5b78dca4
Create Date: 2024-01-25 16:18:35.740780

"""

from enum import StrEnum

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d241d8c493fb"
down_revision = "de0f5b78dca4"
branch_labels = None
depends_on = None


class Workflow(StrEnum):
    BALSAMIC: str = "balsamic"
    BALSAMIC_QC: str = "balsamic-qc"
    BALSAMIC_UMI: str = "balsamic-umi"
    BALSAMIC_PON: str = "balsamic-pon"
    DEMULTIPLEX: str = "demultiplex"
    FASTQ: str = "fastq"
    FLUFFY: str = "fluffy"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"
    RAREDISEASE: str = "raredisease"
    RNAFUSION: str = "rnafusion"
    RSYNC: str = "rsync"
    SARS_COV_2: str = "sars-cov-2"
    SPRING: str = "spring"
    TAXPROFILER: str = "taxprofiler"


def upgrade():
    op.add_column(
        table_name="order",
        column=sa.Column("workflow", sa.Enum(*tuple(Workflow)), nullable=False),
    )


def downgrade():
    op.drop_column(
        table_name="order",
        column_name="workflow",
    )
