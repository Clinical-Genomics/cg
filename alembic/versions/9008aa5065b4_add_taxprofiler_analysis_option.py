"""Add taxprofiler analysis option

Revision ID: 9008aa5065b4
Revises: df1b3dd317d0
Create Date: 2023-04-19 13:46:29.137152

"""
from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "9008aa5065b4"
down_revision = "df1b3dd317d0"
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
    "rnafusion",
    "rsync",
    "sars-cov-2",
    "spring",
)
new_options = sorted(old_options + ("taxprofiler",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
