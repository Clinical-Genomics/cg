"""add-nallo-to-limitations-table

Revision ID: 3a0250e5526d
Revises: 6f368f57df4a
Create Date: 2025-03-06 11:07:29.158959

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a0250e5526d'
down_revision = '6f368f57df4a'
branch_labels = None
depends_on = None


new_workflow = "nallo"

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
    "spring",
    "taxprofiler",
    "tomte",
)

new_options = sorted(old_options + (new_workflow,))

old_analysis_enum = mysql.ENUM(*old_options)
new_analysis_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("application_limitations", "workflow", type_=new_analysis_enum)


def downgrade():
    op.alter_column("application_limitations", "workflow", type_=old_analysis_enum)
