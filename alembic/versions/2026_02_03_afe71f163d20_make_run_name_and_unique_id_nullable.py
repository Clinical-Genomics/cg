"""Make run name and unique id nullable

Revision ID: afe71f163d20
Revises: bd1b231198e4
Create Date: 2026-02-03 09:47:10.272516

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "afe71f163d20"
down_revision = "bd1b231198e4"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_name",
        nullable=False,
        existing_type=sa.String(64),
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unique_id",
        nullable=False,
        existing_type=sa.String(64),
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_id",
        nullable=False,
        existing_type=sa.String(64),
    )


def downgrade():
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_id",
        nullable=True,
        existing_type=sa.String(64),
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="unique_id",
        nullable=True,
        existing_type=sa.String(64),
    )
    op.alter_column(
        table_name="pacbio_sequencing_run",
        column_name="run_name",
        nullable=True,
        existing_type=sa.String(64),
    )
