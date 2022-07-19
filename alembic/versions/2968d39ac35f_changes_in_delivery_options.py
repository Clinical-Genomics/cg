"""Modifies available delivery options

Revision ID: 2968d39ac35f
Revises: ddc94088be4d
Create Date: 2022-07-19 13:34:18.685207

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "2968d39ac35f"
down_revision = "ddc94088be4d"
branch_labels = None
depends_on = None

old_options = (
    "analysis",
    "analysis-bam",
    "fastq",
    "fastq_qc",
    "fastq_qc-analysis",
    "fastq_qc-analysis-cram",
    "fastq_qc-analysis-cram-scout",
    "nipt-viewer",
    "scout",
)
new_options = sorted(
    old_options
    + (
        "fastq_analysis",
        "fastq_analysis_scout",
        "analysis_scout",
    )
)
old_enum = mysql.ENUM(*old_options)
new_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("family", "data_delivery", type_=new_enum)


def downgrade():
    op.alter_column("family", "data_delivery", type_=old_enum)
