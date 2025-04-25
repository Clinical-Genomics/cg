"""add Raredisease ordertype

Revision ID: 039dbdf8af01
Revises: 6362cfd4c61f
Create Date: 2025-04-25 13:57:47.960893

"""

from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from alembic import op

# revision identifiers, used by Alembic.
revision = "039dbdf8af01"
down_revision = "6362cfd4c61f"
branch_labels = None
depends_on = None

Base = declarative_base()


class OrderType(StrEnum):
    BALSAMIC = "balsamic"
    BALSAMIC_UMI = "balsamic-umi"
    FASTQ = "fastq"
    FLUFFY = "fluffy"
    METAGENOME = "metagenome"
    MICROBIAL_FASTQ = "microbial-fastq"
    MICROSALT = "microsalt"
    MIP_DNA = "mip-dna"
    MIP_RNA = "mip-rna"
    NALLO = "nallo"
    PACBIO_LONG_READ = "pacbio-long-read"
    RML = "rml"
    RNAFUSION = "rnafusion"
    SARS_COV_2 = "sars-cov-2"
    TAXPROFILER = "taxprofiler"
    TOMTE = "tomte"


old_order_types = [
    "BALSAMIC",
    "BALSAMIC_UMI",
    "FASTQ",
    "FLUFFY",
    "METAGENOME",
    "MICROBIAL_FASTQ",
    "MICROSALT",
    "MIP_DNA",
    "MIP_RNA",
    "PACBIO_LONG_READ",
    "NALLO",
    "RML",
    "RNAFUSION",
    "SARS_COV_2",
    "TAXPROFILER",
    "TOMTE",
]

new_order_types = old_order_types.copy()
new_order_types.append("RAREDISEASE")
new_order_types.sort()


class OrderTypeApplication(Base):
    """Maps an order type to its allowed applications"""

    __tablename__ = "order_type_application"
    order_type = sa.Column(sa.types.Enum(*list(OrderType)), primary_key=True)


def upgrade():
    op.alter_column(
        table_name="order_type_application",
        column_name="order_type",
        existing_type=sa.Enum(*old_order_types),
        type_=sa.Enum(*new_order_types),
        nullable=False,
    )


def downgrade():
    # Remove incompatible entries
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    for link in session.query(OrderTypeApplication).filter(
        OrderTypeApplication.order_type == "RAREDISEASE"
    ):
        session.delete(link)

    session.commit()

    # Modify the column type back to the old enum
    op.alter_column(
        table_name="order_type_application",
        column_name="order_type",
        existing_type=sa.Enum(*new_order_types),
        type_=sa.Enum(*old_order_types),
        nullable=False,
    )
