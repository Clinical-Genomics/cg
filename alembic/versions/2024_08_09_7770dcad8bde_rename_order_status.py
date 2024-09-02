"""Rename order status
Revision ID: 7770dcad8bde
Revises: bb4c6dbad991
Create Date: 2024-08-09 09:47:47.814700
"""

import sqlalchemy as sa
from sqlalchemy import orm

from alembic import op

# revision identifiers, used by Alembic.
revision = "7770dcad8bde"
down_revision = "bb4c6dbad991"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="order", column_name="is_delivered", type_=sa.Boolean, new_column_name="is_open"
    )
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    for order in session.query("order").all():
        order.is_open = not order.is_open


def downgrade():
    op.alter_column(
        table_name="order", new_column_name="is_delivered", type_=sa.Boolean, column_name="is_open"
    )
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    for order in session.query("order").all():
        order.is_delivered = not order.is_delivered
