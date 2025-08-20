"""Patch CaseSample nullability

Revision ID: e0a3e31ed84e
Revises: 636b19c06a3e
Create Date: 2025-08-20 09:31:21.790773

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e0a3e31ed84e"
down_revision = "636b19c06a3e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="case_sample", column_name="case_id", existing_type=sa.INTEGER(), nullable=False
    )
    op.alter_column(
        table_name="case_sample",
        column_name="sample_id",
        existing_type=sa.INTEGER(),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        table_name="case_sample", column_name="sample_id", existing_type=sa.INTEGER(), nullable=True
    )
    op.alter_column(
        table_name="case_sample", column_name="case_id", existing_type=sa.INTEGER(), nullable=True
    )
