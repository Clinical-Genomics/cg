"""add oncoflow

Revision ID: 203421044513
Revises: 74c5e88cc48e
Create Date: 2026-11-04 15:49:42.319278

"""

from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "203421044513"
down_revision = "74c5e88cc48e"
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
    "oncoflow",
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
