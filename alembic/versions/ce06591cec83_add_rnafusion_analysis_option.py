"""add rnafusion analysis option

Revision ID: ce06591cec83
Revises: 2968d39ac35f
Create Date: 2022-08-30 14:00:17.865006

"""
from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'ce06591cec83'
down_revision = '2968d39ac35f'
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
