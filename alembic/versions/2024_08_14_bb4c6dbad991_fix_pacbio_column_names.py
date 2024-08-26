"""Fix PacBio column names

Revision ID: bb4c6dbad991
Revises: 817cf7fea40d
Create Date: 2024-08-14 14:03:37.122506

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "bb4c6dbad991"
down_revision = "817cf7fea40d"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "pacbio_sequencing_run",
        "hi_fi_reads",
        new_column_name="hifi_reads",
        existing_type=sa.BigInteger(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "hi_fi_yield",
        new_column_name="hifi_yield",
        existing_type=sa.BigInteger(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "run_started_at",
        new_column_name="started_at",
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "run_completed_at",
        new_column_name="completed_at",
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "Productive_ZMWS",
        new_column_name="productive_zmws",
        existing_type=sa.BigInteger(),
    )


def downgrade():
    op.alter_column(
        "pacbio_sequencing_run",
        "productive_zmws",
        new_column_name="Productive_ZMWS",
        existing_type=sa.BigInteger(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "completed_at",
        new_column_name="run_completed_at",
        existing_type=sa.BigInteger(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "started_at",
        new_column_name="run_started_at",
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "hifi_yield",
        new_column_name="hi_fi_yield",
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "hifi_reads",
        new_column_name="hi_fi_reads",
        existing_type=sa.BigInteger(),
    )
