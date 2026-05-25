"""add order id to analysis

Revision ID: 8cd14469c35f
Revises: fabd19666215
Create Date: 2026-05-25 13:11:21.266094

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8cd14469c35f"
down_revision = "fabd19666215"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="analysis",
        column=sa.Column(
            sa.ForeignKey(
                "order.id",
                name="analysis_order_fk",
            ),
            name="order_id",
            type_=sa.Integer,
            nullable=True,
        ),
    )


def downgrade():
    op.drop_constraint(
        constraint_name="analysis_order_fk", table_name="analysis", type_="foreignkey"
    )
    op.drop_column(table_name="analysis", column_name="order_id")
