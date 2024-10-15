"""Add ordertype application table

Revision ID: fd7c9d246255
Revises: 3b165ec34791
Create Date: 2024-10-14 15:29:29.062523

"""

from enum import Enum, auto

import sqlalchemy as sa

from alembic import op
from cg.constants import Workflow

# revision identifiers, used by Alembic.
revision = "fd7c9d246255"
down_revision = "3b165ec34791"
branch_labels = None
depends_on = None


class OrderTypes(Enum):
    BALSAMIC: str = auto()
    BALSAMIC_QC: str = auto()
    BALSAMIC_UMI: str = auto()
    FASTQ: str = auto()
    FLUFFY: str = auto()
    METAGENOME: str = auto()
    MICROBIAL_FASTQ: str = auto()
    MICROSALT: str = auto()
    MIP_DNA: str = auto()
    MIP_RNA: str = auto()
    PACBIO_LONG_READ: str = auto()
    RML: str = auto()
    RNAFUSION: str = auto()
    SARS_COV_2: str = auto()
    TAXPROFILER: str = auto()
    TOMTE: str = auto()


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
