"""rename pacbio sequencing runs

Revision ID: 89c82b65bb1b
Revises: 0ef55d6f0e0f
Create Date: 2025-12-16 13:51:06.956480

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "89c82b65bb1b"
down_revision = "0ef55d6f0e0f"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table(
        old_table_name="pacbio_sequencing_run", new_table_name="pacbio_smrt_cell_metrics"
    )


def downgrade():
    op.rename_table(
        old_table_name="pacbio_smrt_cell_metrics", new_table_name="pacbio_sequencing_run"
    )
