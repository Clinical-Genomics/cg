"""Change the col type from Integer to BigInteger for the yield col in the illumina_sample_sequencing_metrics table.

Revision ID: b3c2b0eefe3a
Revises: 951939f0f9b7
Create Date: 2024-07-04 14:44:26.836450

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b3c2b0eefe3a"
down_revision = "951939f0f9b7"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "illumina_sample_sequencing_metrics",
        "yield",
        type_=sa.BigInteger(),
        existing_type=sa.Integer(),
    )


def downgrade():
    op.alter_column(
        "illumina_sample_sequencing_metrics",
        "yield",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
    )
