"""Add ordertype application table

Revision ID: fd7c9d246255
Revises: 3b165ec34791
Create Date: 2024-10-14 15:29:29.062523

"""

from enum import Enum

import sqlalchemy as sa

from alembic import op
from cg.constants import Workflow

# revision identifiers, used by Alembic.
revision = "fd7c9d246255"
down_revision = "3b165ec34791"
branch_labels = None
depends_on = None


class OrderTypes(Enum):
    BALSAMIC: str = "balsamic"
    BALSAMIC_QC: str = "balsamic-qc"
    BALSAMIC_UMI: str = "balsamic-umi"
    FASTQ: str = "fastq"
    FLUFFY: str = "fluffy"
    METAGENOME: str = "metagenome"
    MICROBIAL_FASTQ: str = "microbial-fastq"
    MICROSALT: str = "microsalt"
    MIP_DNA: str = "mip-dna"
    MIP_RNA: str = "mip-rna"
    PACBIO_LONG_READ = "pacbio-long-read"
    RML: str = "rml"
    RNAFUSION: str = "rnafusion"
    SARS_COV_2: str = "sars-cov-2"
    TAXPROFILER: str = "taxprofiler"
    TOMTE: str = "tomte"


order_type_column = sa.Column("order_type", sa.Enum(OrderTypes), index=True, nullable=False)
application_column = sa.Column(
    "application_id",
    sa.Integer(),
    sa.ForeignKey("application.id", ondelete="CASCADE"),
    nullable=False,
)


def upgrade():
    op.create_table(
        "order_type_application",
        order_type_column,
        application_column,
        sa.PrimaryKeyConstraint("order_type", "application_id"),
    )


def downgrade():
    op.drop_table(table_name="order_type_application")
