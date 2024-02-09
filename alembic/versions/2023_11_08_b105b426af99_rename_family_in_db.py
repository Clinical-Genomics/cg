"""Rename family in db

Revision ID: b105b426af99
Revises: 70e641d723b3
Create Date: 2023-11-08 15:13:25.197537

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b105b426af99"
down_revision = "70e641d723b3"
branch_labels = None
depends_on = None


def upgrade():
    # Drop foreign key constraints that reference the unique constraint to be dropped
    op.drop_constraint("analysis_ibfk_1", "analysis", type_="foreignkey")
    op.drop_constraint("family_sample_ibfk_1", "family_sample", type_="foreignkey")

    # Rename tables
    op.rename_table("family", "case")
    op.rename_table("family_sample", "case_sample")

    # Rename foreign keys
    op.alter_column("analysis", "family_id", new_column_name="case_id", existing_type=sa.Integer())
    op.alter_column(
        "case_sample", "family_id", new_column_name="case_id", existing_type=sa.Integer()
    )

    # Drop the unique constraint
    op.drop_constraint("_family_sample_uc", "case_sample", type_="unique")

    # Create the new unique constraint
    op.create_unique_constraint("_case_sample_uc", "case_sample", ["case_id", "sample_id"])

    # Recreate foreign key constraints referencing the new unique constraint
    op.create_foreign_key("analysis_ibfk_1", "analysis", "case", ["case_id"], ["id"])
    op.create_foreign_key("case_sample_ibfk_1", "case_sample", "case", ["case_id"], ["id"])


def downgrade():
    # Drop foreign key constraints before renaming them back
    op.drop_constraint("analysis_ibfk_1", "analysis", type_="foreignkey")
    op.drop_constraint("case_sample_ibfk_1", "case_sample", type_="foreignkey")

    # Drop the unique constraint
    op.drop_constraint("_case_sample_uc", "case_sample", type_="unique")

    # Rename foreign keys back to original before renaming tables
    op.alter_column("analysis", "case_id", new_column_name="family_id", existing_type=sa.Integer())
    op.alter_column(
        "case_sample", "case_id", new_column_name="family_id", existing_type=sa.Integer()
    )

    # Rename tables back to original
    op.rename_table("case", "family")
    op.rename_table("case_sample", "family_sample")

    # Recreate the original unique constraint
    op.create_unique_constraint("_family_sample_uc", "family_sample", ["family_id", "sample_id"])

    # Recreate foreign key constraints referencing the original unique constraint
    op.create_foreign_key("analysis_ibfk_1", "analysis", "family", ["family_id"], ["id"])
    op.create_foreign_key("family_sample_ibfk_1", "family_sample", "family", ["family_id"], ["id"])
