"""Add lims_workflow_id to application table

Revision ID: 29939ae3d960
Revises: 8cd14469c35f
Create Date: 2026-06-01 15:22:32.469192

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "29939ae3d960"
down_revision = "8cd14469c35f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="application",
        column=sa.Column(
            name="lims_workflow_id",
            type_=sa.Integer,
            nullable=True,
            default=None,
        ),
    )


def downgrade():
    op.drop_column(table_name="application", column_name="lims_workflow_id")
