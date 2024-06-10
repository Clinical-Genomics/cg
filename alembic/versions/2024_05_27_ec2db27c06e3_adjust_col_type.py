"""adjust-col-type

Revision ID: ec2db27c06e3
Revises: 18e3b2aba252
Create Date: 2024-05-27 08:47:58.856322

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ec2db27c06e3"
down_revision = "18e3b2aba252"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="illumina_sequencing_run",
        column_name="yield_q30",
        type_=sa.types.BigInteger(),
        existing_type=sa.types.Float(),
    )


def downgrade():
    op.alter_column(
        table_name="illumina_sequencing_run",
        column_name="yield_q30",
        type_=sa.types.Float(),
        existing_type=sa.types.BigInteger(),
    )
