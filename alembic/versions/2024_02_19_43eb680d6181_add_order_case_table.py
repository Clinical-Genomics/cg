"""Add order case table

Revision ID: 43eb680d6181
Revises: d241d8c493fb
Create Date: 2024-02-19 10:13:21.075891

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "43eb680d6181"
down_revision = "d241d8c493fb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "order_case",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("order_id", sa.Integer, nullable=False),
        sa.Column("case_id", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["case.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("order_id", "case_id", name="_order_case_uc"),
    )


def downgrade():
    op.drop_table(table_name="order_case")
