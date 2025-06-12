"""Rename sequencing qc column

Revision ID: 2a2c618967af
Revises: b3c2b0eefe3a
Create Date: 2024-07-02 13:46:02.090345

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2a2c618967af"
down_revision = "b3c2b0eefe3a"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="case",
        column_name="sequencing_qc_status",
        new_column_name="aggregated_sequencing_qc",
        existing_type=sa.Enum("PASSED", "FAILED", "PENDING"),
    )


def downgrade():
    op.alter_column(
        table_name="case",
        column_name="aggregated_sequencing_qc",
        new_column_name="sequencing_qc_status",
        existing_type=sa.Enum("PASSED", "FAILED", "PENDING"),
    )
