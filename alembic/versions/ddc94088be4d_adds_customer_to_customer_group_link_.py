"""Adds customer to customer_group link table

Revision ID: ddc94088be4d
Revises: 367813f2e597
Create Date: 2022-06-29 15:11:08.142445

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

revision = "ddc94088be4d"
down_revision = "367813f2e597"
branch_labels = None
depends_on = None

Base = declarative_base()


class CustomerGroup(Base):
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)

    customers = sa.orm.relationship(Customer, backref="customer_group", order_by="-Customer.id")


class CustomerLink(Base):
    __table_args__ = (sa.UniqueConstraint("viewer_id", "owner_id", name="_cust_link_uc"),)
    id = Column(types.Integer, primary_key=True)
    viewer_id = Column(sa.ForeignKey("customer.id"))
    owner_id = Column(sa.ForeignKey("customer.id"))
    viewer = sa.orm.relationship("Customer")
    owner = sa.orm.relationship("Customer")


def upgrade():
    op.create_table("customer_link", Column("id", types.Integer, primary_key=True))
    op.create_foreign_key(
        source_table="customer",
        referent_table="customer_link",
    )
    pass


def downgrade():
    pass
