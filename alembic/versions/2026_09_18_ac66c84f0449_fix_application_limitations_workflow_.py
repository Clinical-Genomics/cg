"""Fix application limitations workflow enum

Revision ID: ac66c84f0449
Revises: 8a0dd32c2550
Create Date: 2026-09-18 15:44:19.702564

"""

from sqlalchemy.dialects import mysql

from alembic import op

revision = "ac66c84f0449"
down_revision = "8a0dd32c2550"
branch_labels = None
depends_on = None


# Outdated Enum accidentally reinstated by add_nallo_to_limitations_table
outdated_workflow_list = (
    "balsamic",
    "balsamic-pon",
    "balsamic-qc",
    "balsamic-umi",
    "demultiplex",
    "fastq",
    "fluffy",
    "jasen",
    "microsalt",
    "mip-dna",
    "mip-rna",
    "mutant",
    "nallo",
    "raredisease",
    "rnafusion",
    "rsync",
    "spring",
    "taxprofiler",
    "tomte",
)

# Matches the current Workflow enum (cg/constants/constants.py)
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
)

outdated_enum = mysql.ENUM(*outdated_workflow_list)
current_enum = mysql.ENUM(*current_workflow_list)


def upgrade():
    op.alter_column("application_limitations", "workflow", type_=current_enum)


def downgrade():
    op.alter_column("application_limitations", "workflow", type_=outdated_enum)
