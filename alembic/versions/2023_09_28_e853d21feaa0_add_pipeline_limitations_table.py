"""Add pipeline limitations table

Revision ID: e853d21feaa0
Revises: 9def7a6eae73
Create Date: 2023-09-28 10:13:37.226849

"""

from enum import StrEnum

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e853d21feaa0"
down_revision = "9def7a6eae73"
branch_labels = None
depends_on = None

table_name = "application_limitations"


class Pipeline(StrEnum):
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
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("application.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pipeline", sa.Enum(*list(Pipeline)), nullable=False),
        sa.Column("limitations", sa.Text()),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table(table_name)
