"""Add sequencing qc to case

Revision ID: 37224833a73a
Revises: ec2db27c06e3
Create Date: 2024-05-27 11:11:34.637752

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "37224833a73a"
down_revision = "ec2db27c06e3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "case",
        sa.Column(
            "sequencing_qc_status",
            sa.Enum("FAILED", "PASSED", "PENDING", name="sequencingqcstatus"),
            nullable=False,
            server_default="PENDING",
        ),
    )


def downgrade():
    op.drop_column("case", "sequencing_qc_status")
