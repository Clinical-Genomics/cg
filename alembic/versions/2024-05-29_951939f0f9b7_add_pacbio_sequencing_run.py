"""add_pacbio_sequencing_run

Revision ID: 951939f0f9b7
Revises: 6c98ed61b29e
Create Date: 2024-05-29 14:03:54.754736

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "951939f0f9b7"
down_revision = "6c98ed61b29e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pacbio_sequencing_run",
        sa.Column(
            "id", sa.Integer(), sa.ForeignKey("instrument_run.id"), nullable=False, primary_key=True
        ),
        sa.Column("well", sa.String(length=32), nullable=False),
        sa.Column("plate", sa.Integer, nullable=False),
        sa.Column("movie_time_hours", sa.Integer(), nullable=False),
        sa.Column("hi_fi_reads", sa.BigInteger(), nullable=False),
        sa.Column("hi_fi_yield", sa.BigInteger(), nullable=False),
        sa.Column("hifi_mean_read_length", sa.BigInteger(), nullable=False),
        sa.Column("hifi_median_read_quality", sa.String(length=32), nullable=False),
        sa.Column("percent_reads_passing_q30", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("p0_percent", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("p1_percent", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("p2_percent", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("polymerase_mean_read_length", sa.BigInteger(), nullable=False),
        sa.Column("polymerase_read_length_n50", sa.BigInteger(), nullable=False),
        sa.Column("polymerase_mean_longest_subread", sa.BigInteger(), nullable=False),
        sa.Column("polymerase_longest_subread_n50", sa.BigInteger(), nullable=False),
        sa.Column("control_reads", sa.BigInteger(), nullable=False),
        sa.Column("control_mean_read_length", sa.BigInteger(), nullable=False),
        sa.Column(
            "control_mean_read_concordance", sa.Numeric(precision=6, scale=2), nullable=False
        ),
        sa.Column(
            "control_mode_read_concordance", sa.Numeric(precision=6, scale=2), nullable=False
        ),
    )


def downgrade():
    op.drop_table("pacbio_sequencing_run")
