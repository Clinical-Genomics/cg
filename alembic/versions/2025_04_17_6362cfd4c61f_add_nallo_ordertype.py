"""add Nallo ordertype

Revision ID: 6362cfd4c61f
Revises: 3a0250e5526d
Create Date: 2025-04-17 10:42:20.943466

"""

from sqlalchemy import Enum

from alembic import op

# revision identifiers, used by Alembic.
revision = "6362cfd4c61f"
down_revision = "3a0250e5526d"
branch_labels = None
depends_on = None


base_options = (
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
    "RML",
    "RNAFUSION",
    "SARS_COV_2",
    "TAXPROFILER",
    "TOMTE",
)

old_options = sorted(base_options)
new_options = sorted(old_options + ("NALLO",))


old_order_type_enum = Enum(*old_options)
new_order_type_enum = Enum(*new_options)


def upgrade():
    op.alter_column(
        "order_type_application",
        "order_type",
        existing_type=old_order_type_enum,
        type_=new_order_type_enum,
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "order_type_application",
        "order_type",
        existing_type=new_order_type_enum,
        type_=old_order_type_enum,
        existing_nullable=False,
    )
