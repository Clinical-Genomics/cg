"""drop calc reads columns

Revision ID: 201b16c45366
Revises: 68e54d17f4f3
Create Date: 2023-08-01 09:54:13.113496

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "201b16c45366"
down_revision = "68e54d17f4f3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column(table_name="sample", column_name="calculated_read_count")


def downgrade():
    op.add_column(
        table_name="sample", column=sa.Column("calculated_read_count", sa.BigInteger(), default=0)
    )
