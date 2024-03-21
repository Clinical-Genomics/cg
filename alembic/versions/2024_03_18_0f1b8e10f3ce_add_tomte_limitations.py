"""add tomte limitations

Revision ID: 0f1b8e10f3ce
Revises: 30f8b6634257
Create Date: 2024-03-18 16:47:26.750581

"""

from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0f1b8e10f3ce"
down_revision = "30f8b6634257"
branch_labels = None
depends_on = None


new_workflow = "tomte"

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
)

new_options = sorted(old_options + (new_workflow,))

old_analysis_enum = mysql.ENUM(*old_options)
new_analysis_enum = mysql.ENUM(*new_options)


def upgrade():
    op.alter_column("application_limitations", "workflow", type_=new_analysis_enum)


def downgrade():
    op.alter_column("application_limitations", "workflow", type_=old_analysis_enum)
