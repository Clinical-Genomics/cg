"""add data analysis PON option

Revision ID: 9c9ca9407227
Revises: ddc94088be4d
Create Date: 2022-07-22 18:36:14.853146

"""
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "9c9ca9407227"
down_revision = "ddc94088be4d"
branch_labels = None
depends_on = None

old_options = (
    "balsamic",
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
new_options = sorted(old_options + ("balsamic-pon",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
