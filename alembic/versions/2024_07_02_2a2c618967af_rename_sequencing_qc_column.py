"""Rename sequencing qc column

Revision ID: 2a2c618967af
Revises: 6c98ed61b29e
Create Date: 2024-07-02 13:46:02.090345

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2a2c618967af"
down_revision = "951939f0f9b7"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="case",
        column_name="sequencing_qc_status",
        new_column_name="aggregated_sequencing_qc",
    )


def downgrade():
    op.alter_column(
        table_name="case",
        column_name="aggregated_sequencing_qc",
        new_column_name="sequencing_qc_status",
    )
