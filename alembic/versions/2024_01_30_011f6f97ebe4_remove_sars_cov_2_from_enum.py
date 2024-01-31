"""remove_sars-cov-2_from_enum

Revision ID: 011f6f97ebe4
Revises: d241d8c493fb
Create Date: 2024-01-30 17:08:46.436862

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "011f6f97ebe4"
down_revision = "d241d8c493fb"
branch_labels = None
depends_on = None


old_options = [
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
    "sars-cov-2",
    "spring",
    "taxprofiler",
]
new_options = old_options
new_options.remove("sars-cov-2")

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("case", "data_analysis", type_=mysql.VARCHAR(64), existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=mysql.VARCHAR(64), existing_nullable=True)

    op.alter_column("case", "data_analysis", type_=new_enum, existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=new_enum, existing_nullable=True)


def downgrade():
    op.alter_column("case", "data_analysis", type_=mysql.VARCHAR(64), existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=mysql.VARCHAR(64), existing_nullable=True)

    op.alter_column("case", "data_analysis", type_=old_enum, existing_nullable=True)
    op.alter_column("analysis", "pipeline", type_=old_enum, existing_nullable=True)
