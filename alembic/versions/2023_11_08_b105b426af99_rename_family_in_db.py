"""Rename family in db

Revision ID: b105b426af99
Revises: 70e641d723b3
Create Date: 2023-11-08 15:13:25.197537

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b105b426af99"
down_revision = "70e641d723b3"
branch_labels = None
depends_on = None


def upgrade():
    # Rename tables
    op.rename_table("family", "case")
    op.rename_table("family_sample", "case_sample")

    # Rename foreign keys
    op.alter_column("analysis", "family_id", new_column_name="case_id", type=sa.Integer())
    op.alter_column("case_sample", "family_id", new_column_name="case_id", type=sa.Integer())

    # Rename unique constraint
    op.drop_constraint("_family_sample_uc", "case_sample", type_="unique")
    op.create_unique_constraint("_case_sample_uc", "case_sample", ["case_id", "sample_id"])


def downgrade():
    # Rename tables
    op.rename_table("case", "family")
    op.rename_table("case_sample", "family_sample")

    # Rename foreign keys
    op.alter_column("analysis", "case_id", new_column_name="family_id", type=sa.Integer())
    op.alter_column("family_sample", "case_id", new_column_name="family_id", type=sa.Integer())

    # Rename unique constraint
    op.drop_constraint("_case_sample_uc", "family_sample", type_="unique")
    op.create_unique_constraint("_family_sample_uc", "family_sample", ["family_id", "sample_id"])
