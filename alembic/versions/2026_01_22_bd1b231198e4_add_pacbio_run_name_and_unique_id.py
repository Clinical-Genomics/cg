"""Add Pacbio run name and unique id

Revision ID: bd1b231198e4
Revises: 35132fa0c4ea
Create Date: 2026-01-22 13:09:47.820455

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "bd1b231198e4"
down_revision = "35132fa0c4ea"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_name",
        new_column_name="run_id",
        existing_type=sa.String(64),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("run_name", sa.String(64), nullable=True, index=True),
    )
    op.add_column(
        table_name="pacbio_sequencing_run",
        column=sa.Column("unique_id", sa.String(64), nullable=True, unique=True),
    )


def downgrade():
    op.drop_column(table_name="pacbio_sequencing_run", column_name="unique_id")
    op.drop_column(table_name="pacbio_sequencing_run", column_name="run_name")
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_id",
        new_column_name="run_name",
        existing_type=sa.String(64),
    )
