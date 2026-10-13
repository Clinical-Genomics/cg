"""add-trana-to-workflow

Revision ID: dbcd93acdda1
Revises: 5d9d60b45012
Create Date: 2026-10-06 10:39:26.494073

"""

from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "dbcd93acdda1"
down_revision = "5d9d60b45012"
branch_labels = None
depends_on = None

outdated_workflow_list = (
    "balsamic",
    "balsamic-pon",
    "balsamic-umi",
    "demultiplex",
    "fluffy",
    "jasen",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "nallo",
    "raredisease",
    "raw-data",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
)

current_workflow_list = (
    "balsamic",
    "balsamic-pon",
    "balsamic-umi",
    "demultiplex",
    "fluffy",
    "jasen",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "nallo",
    "raredisease",
    "raw-data",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
    "trana",
)

outdated_enum = mysql.ENUM(*outdated_workflow_list)
current_enum = mysql.ENUM(*current_workflow_list)


def upgrade():
    op.alter_column("application_limitations", "workflow", type_=current_enum)
    op.alter_column("analysis", "workflow", type_=current_enum)
    op.alter_column("case", "data_analysis", type_=current_enum)


def downgrade():
    op.alter_column("application_limitations", "workflow", type_=outdated_enum)
    op.alter_column("analysis", "workflow", type_=outdated_enum)
    op.alter_column("case", "data_analysis", type_=outdated_enum)
