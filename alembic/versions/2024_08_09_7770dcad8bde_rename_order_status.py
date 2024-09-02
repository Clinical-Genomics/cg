"""Rename order status
Revision ID: 7770dcad8bde
Revises: bb4c6dbad991
Create Date: 2024-08-09 09:47:47.814700
"""

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from alembic import op

# revision identifiers, used by Alembic.
revision = "7770dcad8bde"
down_revision = "bb4c6dbad991"
branch_labels = None
depends_on = None


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_open: Mapped[str]


def upgrade():
    op.alter_column(
        table_name="order", column_name="is_delivered", type_=sa.Boolean, new_column_name="is_open"
    )
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    for order in session.query(Order).all():
        order.is_open = not order.is_open
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    for order in session.query(Order).all():
        order.is_open = not order.is_open
    session.commit()
    op.alter_column(
        table_name="order", new_column_name="is_delivered", type_=sa.Boolean, column_name="is_open"
    )
