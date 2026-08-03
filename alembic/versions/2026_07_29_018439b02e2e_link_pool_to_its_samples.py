"""Link pool to its samples

Revision ID: 018439b02e2e
Revises: eb2e90a251c5
Create Date: 2026-07-29 14:48:27.610420

"""

from datetime import datetime
from typing import Annotated

import sqlalchemy as sa
from sqlalchemy import update
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    joinedload,
    mapped_column,
    relationship,
    selectinload,
)

from alembic import op

# revision identifiers, used by Alembic.
revision = "018439b02e2e"
down_revision = "eb2e90a251c5"
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


order_case = sa.Table(
    "order_case",
    Base.metadata,
    sa.Column("order_id", sa.ForeignKey("order.id", ondelete="CASCADE"), nullable=False),
    sa.Column("case_id", sa.ForeignKey("case.id", ondelete="CASCADE"), nullable=False),
    sa.UniqueConstraint("order_id", "case_id", name="_order_case_uc"),
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


class Order(Base):
    """Model for storing orders."""

    __tablename__ = "order"

    id: Mapped[PrimaryKeyInt]
    order_date: Mapped[datetime] = mapped_column(default=datetime.now)
    ticket_id: Mapped[int] = mapped_column(unique=True, index=True)
    is_open: Mapped[bool] = mapped_column(default=True)

    pools: Mapped[list["Pool"]] = relationship(
        back_populates="db_order", order_by="Pool.ordered_at"
    )

    cases: Mapped[list[Case]] = relationship(secondary=order_case, back_populates="orders")


class Pool(Base):
    __tablename__ = "pool"
    id: Mapped[PrimaryKeyInt]
    order_id: Mapped[int] = mapped_column(sa.ForeignKey("order.id"))
    db_order: Mapped[Order] = relationship(back_populates="pools", foreign_keys=[order_id])
    ordered_at: Mapped[datetime]
    samples: Mapped[list["Sample"]] = relationship(back_populates="pool")


class Sample(Base):
    __tablename__ = "sample"
    id: Mapped[PrimaryKeyInt]
    internal_id: Mapped[str]
    links: Mapped[list[CaseSample]] = relationship(back_populates="sample")
    pool_id: Mapped[int | None] = mapped_column(sa.ForeignKey("pool.id"))
    pool: Mapped[Pool] = relationship(back_populates="samples", foreign_keys=[pool_id])


def upgrade():
    bind: sa.Connection = op.get_bind()
    session = Session(bind=bind)
    op.add_column(
        table_name="sample",
        column=sa.Column(
            sa.ForeignKey(
                "pool.id",
                name="sample_pool_fk",
            ),
            name="pool_id",
            type_=sa.Integer,
            nullable=True,
        ),
    )
    pools = session.query(Pool).options(
        selectinload(Pool.samples),
        joinedload(Pool.db_order).selectinload(Order.pools),
        joinedload(Pool.db_order)
        .selectinload(Order.cases)
        .selectinload(Case.links)
        .selectinload(CaseSample.sample),
    )
    mappings = []
    for pool in pools.all():
        db_order: Order = pool.db_order
        if db_order.pools == [pool]:
            cases: list[Case] = db_order.cases
            samples: list[Sample] = [sample for case in cases for sample in case.samples]
            mappings.extend({"id": sample.id, "pool_id": pool.id} for sample in samples)
    session.execute(update(Sample), mappings)
    session.commit()


def downgrade():
    op.drop_constraint(constraint_name="sample_pool_fk", table_name="sample", type_="foreignkey")
    op.drop_column(table_name="sample", column_name="pool_id")
