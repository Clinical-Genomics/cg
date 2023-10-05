"""add fastq_qc-analysis option to data delivery

Revision ID: c76d655c8edf
Revises: f2edbd530656
Create Date: 2022-01-28 13:58:30.565056

"""
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "c76d655c8edf"
down_revision = "f2edbd530656"
branch_labels = None
depends_on = None


old_options = (
    "analysis",
    "analysis-bam",
    "fastq",
    "fastq_qc",
    "fastq_qc-analysis-cram",
    "fastq_qc-analysis-cram-scout",
    "nipt-viewer",
    "scout",
)
new_options = sorted(old_options + ("fastq_qc-analysis",))
old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_delivery", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_delivery", type_=old_enum)
