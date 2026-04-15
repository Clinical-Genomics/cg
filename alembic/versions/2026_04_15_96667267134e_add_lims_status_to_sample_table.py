"""Add LIMS status to Sample table

Revision ID: 96667267134e
Revises: ea37e15dd9c6
Create Date: 2026-04-15 10:29:40.832895

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "96667267134e"
down_revision = "ea37e15dd9c6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="sample",
        column=sa.Column(
            name="lims_status",
            type_=sa.Enum(*["pending", "top-up", "re-prep", "done"]),
            nullable=False,
            default="pending",
            index=True,
            unique=False,
        ),
    )


def downgrade():
    op.drop_column(table_name="sample", column_name="lims_status")
