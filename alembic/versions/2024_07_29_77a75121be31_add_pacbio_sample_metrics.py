"""Add PacBio sample metrics model

Revision ID: 77a75121be31
Revises: 0808675ad136
Create Date: 2024-07-29 09:17:26.602759

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "77a75121be31"
down_revision = "0808675ad136"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pacbio_sample_run_metrics",
        sa.Column("id", sa.Integer(), sa.ForeignKey("sample_run_metrics.id"), primary_key=True),
        sa.Column("hifi_reads", sa.BigInteger(), nullable=False),
        sa.Column("hifi_yield", sa.BigInteger(), nullable=False),
        sa.Column("hifi_mean_read_length", sa.BigInteger(), nullable=False),
        sa.Column("hifi_median_read_quality", sa.String(length=32), nullable=False),
        sa.Column("percent_reads_passing_q30", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("failed_reads", sa.BigInteger(), nullable=False),
        sa.Column("failed_yield", sa.BigInteger(), nullable=False),
        sa.Column("failed_mean_read_length", sa.BigInteger(), nullable=False),
    )
    op.add_column(
        "pacbio_sequencing_run", sa.Column("failed_reads", sa.BigInteger(), nullable=False)
    )
    op.add_column(
        "pacbio_sequencing_run",
        sa.Column("failed_yield", sa.BigInteger(), nullable=False),
    )
    op.add_column(
        "pacbio_sequencing_run",
        sa.Column("failed_mean_read_length", sa.BigInteger(), nullable=False),
    )
    op.add_column(
        "pacbio_sequencing_run",
        sa.Column("movie_name", sa.String(length=32), nullable=False),
    )
    op.add_column(
        "pacbio_sequencing_run",
        sa.Column("Productive_ZMWS", sa.BigInteger(), nullable=False),
    )
    op.alter_column(
        "pacbio_sequencing_run",
        "movie_time_hours",
        existing_type=sa.Integer(),
        existing_nullable=False,
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "pacbio_sequencing_run",
        "movie_time_hours",
        existing_type=sa.Integer(),
        existing_nullable=True,
        nullable=False,
    )
    op.drop_column("pacbio_sequencing_run", "failed_reads")
    op.drop_column("pacbio_sequencing_run", "failed_yield")
    op.drop_column("pacbio_sequencing_run", "failed_mean_read_length")
    op.drop_column("pacbio_sequencing_run", "movie_name")
    op.drop_column("pacbio_sequencing_run", "Productive_ZMWS")
    op.drop_table("pacbio_sample_run_metrics")
