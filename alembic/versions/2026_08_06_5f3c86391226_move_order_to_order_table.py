"""Move order to order table

Revision ID: 5f3c86391226
Revises: d2900fdde3e8
Create Date: 2026-08-06 11:11:15.435937

"""

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
    order: Mapped[str | None]
    cases: Mapped[list["Case"]] = relationship(secondary=order_case, back_populates="orders")
    name: Mapped[str | None]
    ticket_id: Mapped[int]


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


def upgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.add_column(
        table_name="order",
        column=sa.Column(
            name="name",
            type_=mysql.VARCHAR(64),
        ),
    )
    orders = session.query(Order).options(
        selectinload(Order.cases).selectinload(Case.links).selectinload(CaseSample.sample)
    )

    for order in orders.all():
        for case in order.cases:
            for sample in case.samples:
                if sample.original_ticket == str(order.ticket_id):
                    order.name = sample.order
                    session.add(order)
                    break


def downgrade():
    pass
