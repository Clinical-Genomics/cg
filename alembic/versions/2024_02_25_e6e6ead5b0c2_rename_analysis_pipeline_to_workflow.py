"""rename_analysis_pipeline_to_workflow

Revision ID: e6e6ead5b0c2
Revises: 43eb680d6181
Create Date: 2024-02-25 13:09:07.378619

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e6e6ead5b0c2"
down_revision = "43eb680d6181"
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
        "analysis",
        "pipeline",
        new_column_name="workflow",
        existing_type=sa.Enum(*list(workflow)),
    )

    op.alter_column(
        "analysis",
        "pipeline_version",
        new_column_name="workflow_version",
        existing_type=sa.String(32),
    )


def downgrade():
    op.alter_column(
        "analysis",
        "workflow",
        new_column_name="pipeline",
        existing_type=sa.Enum(*list(workflow)),
    )

    op.alter_column(
        "analysis",
        "workflow_version",
        new_column_name="pipeline_version",
        existing_type=sa.String(32),
    )
