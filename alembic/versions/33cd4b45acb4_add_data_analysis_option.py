"""add data analysis option

Revision ID: 33cd4b45acb4
Revises: 367813f2e597
Create Date: 2022-06-28 14:22:15.811222

"""
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "33cd4b45acb4"
down_revision = "367813f2e597"
branch_labels = None
depends_on = None


old_options = (
    "balsamic",
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
new_options = sorted(old_options + ("balsamic-qc",))

old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_analysis", type_=new_enum)
    op.alter_column("analysis", "pipeline", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_analysis", type_=old_enum)
    op.alter_column("analysis", "pipeline", type_=old_enum)
