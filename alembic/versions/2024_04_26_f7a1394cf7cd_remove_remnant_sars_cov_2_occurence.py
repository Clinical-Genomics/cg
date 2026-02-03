"""Remove remnant sars-cov-2 occurence

Revision ID: f7a1394cf7cd
Revises: ac5a804a9f47
Create Date: 2024-04-26 09:52:08.303306

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f7a1394cf7cd"
down_revision = "ac5a804a9f47"
branch_labels = None
depends_on = None

workflow_to_remove = "sars-cov-2"

old_options = (
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
)

# Remove workflow_to_remove from old_options into new_options
new_options = tuple([x for x in old_options if x != workflow_to_remove])

old_analysis_enum = mysql.ENUM(*old_options)
new_analysis_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("order", "workflow", type_=new_analysis_enum)


def downgrade():
    op.alter_column("order", "workflow", type_=old_analysis_enum)
