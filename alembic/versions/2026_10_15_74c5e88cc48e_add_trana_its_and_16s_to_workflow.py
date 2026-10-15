"""add trana its and 16s to workflow

Revision ID: 74c5e88cc48e
Revises: dbcd93acdda1
Create Date: 2026-10-15 10:01:49.341002

"""

from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "74c5e88cc48e"
down_revision = "dbcd93acdda1"
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
    "trana",
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
    "trana-16s",
    "trana-its",
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
