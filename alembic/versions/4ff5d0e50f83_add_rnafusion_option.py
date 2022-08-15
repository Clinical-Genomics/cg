"""add rnafusion option

Revision ID: 4ff5d0e50f83
Revises: bcf73370eece
Create Date: 2022-08-15 13:32:36.965972

"""
from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "4ff5d0e50f83"
down_revision = "9c9ca9407227"
branch_labels = None
depends_on = None

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
    "rsync",
    "sars-cov-2",
    "spring",
)
new_options = sorted(old_options + ("rnafusion",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
