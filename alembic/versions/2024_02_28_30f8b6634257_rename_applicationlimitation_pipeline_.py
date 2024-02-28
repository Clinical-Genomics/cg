"""rename_applicationlimitation_pipeline_to_workflow

Revision ID: 30f8b6634257
Revises: e6e6ead5b0c2
Create Date: 2024-02-28 13:39:41.688160

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "30f8b6634257"
down_revision = "e6e6ead5b0c2"
branch_labels = None
depends_on = None

workflow: list[str] = [
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


def upgrade():
    op.alter_column(
        "application_limitations",
        "pipeline",
        new_column_name="workflow",
        existing_type=sa.Enum(*list(workflow)),
    )


def downgrade():
    op.alter_column(
        "application_limitations",
        "workflow",
        new_column_name="pipeline",
        existing_type=sa.Enum(*list(workflow)),
    )
