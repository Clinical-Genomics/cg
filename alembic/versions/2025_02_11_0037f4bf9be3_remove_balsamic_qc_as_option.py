"""Remove Balsamic-QC as option

Revision ID: 0037f4bf9be3
Revises: a9568bb3a8b7
Create Date: 2025-02-11 09:13:35.303826

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0037f4bf9be3"
down_revision = "a9568bb3a8b7"
branch_labels = None
depends_on = None


old_order_types = [
    "BALSAMIC",
    "BALSAMIC_QC",
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
new_order_types.remove("BALSAMIC_QC")


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
