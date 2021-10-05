"""Add data delivery options

Revision ID: c494649637d5
Revises: 1c27462b49f6
Create Date: 2021-09-28 11:14:47.090453

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "c494649637d5"
down_revision = "1c27462b49f6"
branch_labels = None
depends_on = None

old_options = ("analysis", "analysis-bam", "fastq", "fastq_qc", "nipt-viewer", "scout")
new_options = sorted(
    old_options
    + (
        "fastq_qc-analysis-cram",
        "fastq_qc-analysis-cram-scout",
    )
)
old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_delivery", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_delivery", type_=old_enum)
