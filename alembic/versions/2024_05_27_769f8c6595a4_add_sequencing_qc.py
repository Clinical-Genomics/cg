"""Add sequencing QC

Revision ID: 769f8c6595a4
Revises: ec2db27c06e3
Create Date: 2024-05-27 10:41:06.062540

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "769f8c6595a4"
down_revision = "ec2db27c06e3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "case",
        sa.Column(
            "sequencing_qc_status",
            sa.Enum("FAILED", "PASSED", "PENDING", name="sequencingqcstatus"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("case", "sequencing_qc_status")
