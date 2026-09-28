"""Move compression status from Case to Sample

Revision ID: 5d9d60b45012
Revises: ac66c84f0449
Create Date: 2026-09-28 09:43:05.188646

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "5d9d60b45012"
down_revision = "ac66c84f0449"
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column "skip_compression" on "sample" table (defaults to False)
    op.add_column(
        table_name="sample",
        column=sa.Column(
            name="skip_compression",
            type_=sa.Boolean,
            nullable=False,
            default=False,
        ),
    )

    # Loop through all cases with "is_compressible" = False

    """
    (
        select(Sample)
        .where(
            Sample.id.not_in(incompressible_case_samples_subquery),
            Sample.internal_id.in_(internal_ids),
        )
        .distinct()
        .order_by(Sample.created_at.asc())
    )
    """

    # For all samples such cases, set "skip_compression" to True

    # Remove the "is_compressible" column from "case" table
    pass


def downgrade():
    # Add the "is_compressible" column to the "case" table (defaults to True)

    # Loop over all samples with "skip_compression" = True
    # For all cases of these samples, set "is_compressible" to False

    # Drop the "skip_compression" column from "sample" table
    pass
