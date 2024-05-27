"""add_pacbio_smrt_cell

Revision ID: 6c98ed61b29e
Revises: dc8b9a53d972
Create Date: 2024-05-27 14:17:59.848488

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6c98ed61b29e"
down_revision = "dc8b9a53d972"
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
