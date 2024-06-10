"""add undetermined remove sequenced at

Revision ID: dc8b9a53d972
Revises: 37224833a73a
Create Date: 2024-05-27 13:48:00.330599

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "dc8b9a53d972"
down_revision = "37224833a73a"
branch_labels = None
depends_on = None


def upgrade():
    # remove sequenced_at columns from illumina_sequencing_run
    op.drop_column(table_name="illumina_sequencing_run", column_name="sequenced_at")

    # add percent undetermined reads to illumina_sequencing_run
    op.add_column(
        table_name="illumina_sequencing_run",
        column=sa.Column("percent_undetermined_reads", sa.Float(), nullable=True),
    )


def downgrade():
    # remove percent undetermined reads from illumina_sequencing_run
    op.drop_column(table_name="illumina_sequencing_run", column_name="percent_undetermined_reads")

    # add sequenced_at columns to illumina_sequencing_run
    op.add_column(
        table_name="illumina_sequencing_run",
        column=sa.Column("sequenced_at", sa.DateTime(), nullable=True),
    )
