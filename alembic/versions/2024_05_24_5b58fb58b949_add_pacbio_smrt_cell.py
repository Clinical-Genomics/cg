"""add_pacbio_smrt_cell

Revision ID: 5b58fb58b949
Revises: 18e3b2aba252
Create Date: 2024-05-24 15:54:54.680918

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5b58fb58b949"
down_revision = "18e3b2aba252"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pacbio_smrt_cell",
        sa.Column(
            "id", sa.Integer(), sa.ForeignKey("run_device.id"), nullable=False, primary_key=True
        ),
    )


def downgrade():
    op.drop_table("pacbio_smrt_cell")
