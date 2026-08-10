"""Move order to order table

Revision ID: 5f3c86391226
Revises: d2900fdde3e8
Create Date: 2026-08-06 11:11:15.435937

"""

from datetime import datetime
from typing import Annotated

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
)

from alembic import op

# revision identifiers, used by Alembic.
revision = "5f3c86391226"
down_revision = "d2900fdde3e8"
branch_labels = None
depends_on = None

PrimaryKeyInt = Annotated[int, mapped_column(primary_key=True)]
Str32 = Annotated[str, 32]
Str64 = Annotated[str, 64]


class Base(DeclarativeBase):
    type_annotation_map = {
        Str32: sa.String(32),
        Str64: sa.String(64),
    }


order_case = sa.Table(
    "order_case",
    Base.metadata,
    sa.Column("order_id", sa.ForeignKey("order.id", ondelete="CASCADE"), nullable=False),
    sa.Column("case_id", sa.ForeignKey("case.id", ondelete="CASCADE"), nullable=False),
    sa.UniqueConstraint("order_id", "case_id", name="_order_case_uc"),
)


class Order(Base):
    """Model for storing orders."""

    __tablename__ = "order"

    id: Mapped[PrimaryKeyInt]
    cases: Mapped[list["Case"]] = relationship(secondary=order_case, back_populates="orders")
    name: Mapped[str | None]
    ticket_id: Mapped[int]
    pools: Mapped[list["Pool"]] = relationship(
        back_populates="db_order", order_by="Pool.ordered_at"
    )


class Case(Base):
    __tablename__ = "case"
    id: Mapped[PrimaryKeyInt]
    links: Mapped[list["CaseSample"]] = relationship(back_populates="case")
    orders: Mapped[list["Order"]] = relationship(secondary=order_case, back_populates="cases")

    @property
    def samples(self) -> list["Sample"]:
        """Return case samples."""
        return [link.sample for link in self.links]


class CaseSample(Base):
    __tablename__ = "case_sample"
    id: Mapped[PrimaryKeyInt]
    case_id: Mapped[str] = mapped_column(
        sa.ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    sample_id: Mapped[int] = mapped_column(
        sa.ForeignKey("sample.id", ondelete="CASCADE"), nullable=False
    )
    case: Mapped[Case] = relationship(back_populates="links")
    sample: Mapped["Sample"] = relationship(foreign_keys=[sample_id], back_populates="links")


class Sample(Base):
    __tablename__ = "sample"
    id: Mapped[PrimaryKeyInt]
    internal_id: Mapped[str]
    links: Mapped[list[CaseSample]] = relationship(back_populates="sample")
    order: Mapped[str | None]
    original_ticket: Mapped[str | None]


class Pool(Base):
    __tablename__ = "pool"
    id: Mapped[PrimaryKeyInt]
    order: Mapped[str]
    order_id: Mapped[int] = mapped_column(sa.ForeignKey("order.id"))
    db_order: Mapped[Order] = relationship(back_populates="pools", foreign_keys=[order_id])
    ordered_at: Mapped[datetime]


def upgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.create_index(
        index_name="pool_order_id_ix", table_name="pool", columns=["order_id"]
    )  # This was missing
    op.add_column(
        table_name="order",
        column=sa.Column(name="name", type_=mysql.VARCHAR(64), nullable=True, index=True),
    )
    orders = session.query(Order).options(
        selectinload(Order.cases).selectinload(Case.links).selectinload(CaseSample.sample)
    )

    for order in orders.all():
        for case in order.cases:
            for sample in case.samples:
                if not sample.order:
                    continue
                elif sample.original_ticket == str(order.ticket_id):
                    order.name = sample.order
                    session.add(order)
                    break
                # If unable to match on original ticket, check if it is the only order the sample has been in
                elif len(sample.links) == 1:
                    if len(sample.links[0].case.orders) == 1:
                        order.name = sample.order
                        session.add(order)
                        break
        if not order.name:
            for pool in order.pools:
                if pool.order:
                    order.name = pool.order
    session.commit()
    op.drop_column(table_name="sample", column_name="order")
    op.drop_constraint(constraint_name="_order_name_uc", table_name="pool", type_="unique")
    op.create_unique_constraint(
        constraint_name="_order_name_uc", table_name="pool", columns=["order_id", "name"]
    )
    op.drop_column(table_name="pool", column_name="order")


def downgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.add_column(
        table_name="pool",
        column=sa.Column(name="order", type_=mysql.VARCHAR(64, charset="latin1"), nullable=True),
    )
    op.drop_constraint(constraint_name="_order_name_uc", table_name="pool", type_="unique")
    op.create_unique_constraint(
        constraint_name="order_name_uc", table_name="pool", columns=["order", "name"]
    )
    op.add_column(
        table_name="sample",
        column=sa.Column(name="order", type_=mysql.VARCHAR(64, charset="latin1"), nullable=True),
    )
    orders = session.query(Order).options(
        selectinload(Order.pools),
        selectinload(Order.cases).selectinload(Case.links).selectinload(CaseSample.sample),
    )

    for order in orders.all():
        for case in order.cases:
            for sample in case.samples:
                if sample.order:
                    continue
                elif sample.original_ticket == str(order.ticket_id):
                    sample.order = order.name
                    session.add(sample)
                    break
                # If unable to match on original ticket, check if it is the only order the sample has been in
                elif len(sample.links) == 1:
                    if len(sample.links[0].case.orders) == 1:
                        sample.order = order.name
                        session.add(sample)
                        break
        for pool in order.pools:
            if pool.order:
                continue
            else:
                pool.order = order.name
                session.add(pool)
    session.commit()
    op.alter_column(
        table_name="pool",
        column_name="order",
        existing_type=mysql.VARCHAR(64, charset="latin1"),
        nullable=False,
    )
    op.drop_column(table_name="order", column_name="name")
    op.drop_index(table_name="pool", index_name="pool_order_id_ix")
