"""Drop order id column

Revision ID: b614a52759c5
Revises: 24c1e9e1476d
Create Date: 2024-03-25 15:52:29.658272

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b614a52759c5"
down_revision = "24c1e9e1476d"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(constraint_name="case_ibfk_2", table_name="case")
    op.drop_column("case", "order_id")


def downgrade():
    op.add_column(
        "case",
        sa.Column(
            "order_id", sa.Integer(), sa.ForeignKey("order.id", name="case_ibfk_2"), nullable=True
        ),
    )
