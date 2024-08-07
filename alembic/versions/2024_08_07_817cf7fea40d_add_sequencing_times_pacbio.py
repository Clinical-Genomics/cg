"""Add sequencing times PacBio

Revision ID: 817cf7fea40d
Revises: 601a2f272754
Create Date: 2024-08-07 10:19:57.450266

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "817cf7fea40d"
down_revision = "601a2f272754"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "pacbio_sequencing_run", sa.Column("run_started_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "pacbio_sequencing_run",
        sa.Column("run_completed_at", sa.DateTime(), nullable=True),
    )
    op.drop_column("pacbio_sequencing_run", "movie_time_hours")


def downgrade():
    op.add_column(
        "pacbio_sequencing_run",
        sa.Column("movie_time_hours", sa.Integer(), nullable=True),
    )
    op.drop_column("pacbio_sequencing_run", "run_completed_at")
    op.drop_column("pacbio_sequencing_run", "run_started_at")
