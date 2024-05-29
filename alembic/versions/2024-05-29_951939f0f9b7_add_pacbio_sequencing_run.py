"""add_pacbio_sequencing_run

Revision ID: 951939f0f9b7
Revises: 6c98ed61b29e
Create Date: 2024-05-29 14:03:54.754736

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

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
            "id", sa.Integer(), sa.ForeignKey("run_metrics.id"), nullable=False, primary_key=True
        ),
        ## TODO: Add columns with correct type here
    )


def downgrade():
    op.drop_table("pacbio_sequencing_run")
