"""add Nallo ordertype

Revision ID: 6362cfd4c61f
Revises: 3a0250e5526d
Create Date: 2025-04-17 10:42:20.943466

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6362cfd4c61f"
down_revision = "3a0250e5526d"
branch_labels = None
depends_on = None

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
    "RML",
    "RNAFUSION",
    "SARS_COV_2",
    "TAXPROFILER",
    "TOMTE",
]

new_order_types = old_order_types.copy()
new_order_types.append("NALLO")


def upgrade():
    op.alter_column(
        table_name="order_type_application",
        column_name="order_type",
        existing_type=sa.Enum(*old_order_types),
        type_=sa.Enum(*new_order_types),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        table_name="order_type_application",
        column_name="order_type",
        existing_type=sa.Enum(*new_order_types),
        type_=sa.Enum(*old_order_types),
        nullable=False,
    )
