"""Add tomte to analysis options

Revision ID: b2fcb2ada306
Revises: e6e6ead5b0c2
Create Date: 2024-03-14 17:10:09.156438

"""
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2fcb2ada306"
down_revision = "e6e6ead5b0c2"
branch_labels = None
depends_on = None


new_workflow = "tomte"

old_options: list[str] = [
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
]

new_options = sorted(
    old_options
    + [
        new_workflow,
    ]
)

old_analysis_enum = mysql.ENUM(*old_options)
new_analysis_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("case", "data_analysis", type_=new_analysis_enum)
    op.alter_column("analysis", "workflow", type_=new_analysis_enum)


def downgrade():
    op.alter_column("case", "data_analysis", type_=old_analysis_enum)
    op.alter_column("analysis", "workflow", type_=old_analysis_enum)
