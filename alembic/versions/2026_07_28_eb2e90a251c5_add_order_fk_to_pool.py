"""Add order fk to pool

Revision ID: eb2e90a251c5
Revises: 7e84083f6cb0
Create Date: 2026-07-28 11:38:21.383286

"""

import logging
from datetime import datetime
from typing import Annotated

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from alembic import op

# revision identifiers, used by Alembic.
revision = "eb2e90a251c5"
down_revision = "7e84083f6cb0"
branch_labels = None
depends_on = None

PrimaryKeyInt = Annotated[int, mapped_column(primary_key=True)]
Str32 = Annotated[str, 32]
Str64 = Annotated[str, 64]
Text = Annotated[str, None]


class Base(DeclarativeBase):
    type_annotation_map = {
        Str32: sa.String(32),
        Str64: sa.String(64),
    }


class Customer(Base):
    __tablename__ = "customer"
    id: Mapped[PrimaryKeyInt]


class Order(Base):
    """Model for storing orders."""

    __tablename__ = "order"

    id: Mapped[PrimaryKeyInt]
    customer_id: Mapped[int] = mapped_column(sa.ForeignKey("customer.id"))
    order_date: Mapped[datetime] = mapped_column(default=datetime.now)
    ticket_id: Mapped[int] = mapped_column(unique=True, index=True)
    is_open: Mapped[bool] = mapped_column(default=True)


class Pool(Base):
    __tablename__ = "pool"
    __table_args__ = (sa.UniqueConstraint("order", "name", name="_order_name_uc"),)
    comment: Mapped[Text | None]
    created_at: Mapped[datetime | None] = mapped_column(default=datetime.now)
    customer_id: Mapped[int] = mapped_column(sa.ForeignKey("customer.id"))
    id: Mapped[PrimaryKeyInt]
    name: Mapped[Str32]
    order: Mapped[Str64]
    order_id: Mapped[int] = mapped_column(sa.ForeignKey("order.id"))
    db_order: Mapped[Order] = orm.relationship(foreign_keys=[order_id])
    ordered_at: Mapped[datetime]
    received_at: Mapped[datetime | None]
    ticket: Mapped[Str32 | None]


LOG = logging.getLogger(__name__)


def upgrade():
    """
    Adds a relationship between the Pool and the order table and uses the ticket column to link the two,
    before dropping the (now obsolete) ticket column.
    """
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.add_column(
        table_name="pool",
        column=sa.Column(
            sa.ForeignKey(
                "order.id",
                name="pool_order_fk",
            ),
            name="order_id",
            type_=sa.Integer,
            nullable=True,
        ),
    )
    for pool in session.query(Pool).all():
        if pool.ticket:
            order: Order | None = session.query(Order).filter_by(ticket_id=int(pool.ticket)).first()
            if pool.ticket and not order:
                LOG.info(f"Creating order with ticket_id {pool.ticket}")
                order = Order(
                    customer_id=pool.customer_id,
                    is_open=False,
                    order_date=pool.ordered_at,
                    ticket_id=int(pool.ticket),
                )
                session.add(order)
            if order:
                pool.db_order = order
            session.add(pool)
    session.commit()
    op.drop_column(table_name="pool", column_name="ticket")


def downgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.add_column(
        table_name="pool", column=sa.Column(name="ticket", type_=sa.VARCHAR(32), nullable=True)
    )
    for pool in session.query(Pool):
        if pool.db_order:
            pool.ticket = str(pool.db_order.ticket_id)
            session.add(pool)
    session.commit()
    op.drop_constraint(constraint_name="pool_order_fk", table_name="pool", type_="foreignkey")
    op.drop_column(table_name="pool", column_name="order_id")
