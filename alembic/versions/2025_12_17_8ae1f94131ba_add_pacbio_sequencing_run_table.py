"""Add Pacbio Sequencing Run table

Revision ID: 8ae1f94131ba
Revises: 89c82b65bb1b
Create Date: 2025-12-17 10:14:48.011962

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8ae1f94131ba"
down_revision = "89c82b65bb1b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pacbio_sequencing_run",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("run_name", sa.VARCHAR(64), nullable=False, unique=True),
        sa.Column("processed", sa.Boolean, nullable=False, default=False),
        sa.Column("comment", sa.Text, nullable=False, default=""),
        sa.Column("instrument_name", sa.Enum("Wilma", "Betty"), nullable=False),
    )


def downgrade():
    pass
