"""Adds customer to customer_group link table

Revision ID: ddc94088be4d
Revises: 367813f2e597
Create Date: 2022-06-29 15:11:08.142445

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy.dialects import mysql
from sqlalchemy import Column, types, orm
from sqlalchemy.ext.declarative import declarative_base

revision = "ddc94088be4d"
down_revision = "367813f2e597"
branch_labels = None
depends_on = None

Base = declarative_base()

customer_group_links = sa.Table(
    "customer_group_links",
    Base.metadata,
    Column("customer_id", types.Integer, sa.ForeignKey("customer.id"), nullable=False),
    Column("customer_group_id", types.Integer, sa.ForeignKey("customer_group.id"), nullable=False),
    sa.UniqueConstraint("customer_id", "customer_group_id", name="_customer_group_link_uc"),
)


class Customer(Base):
    __tablename__ = "customer"
    id = Column(types.Integer, primary_key=True)
    customer_group_id = Column(sa.ForeignKey("customer_group.id"), nullable=False)
    customer_groups = orm.relationship("CustomerGroup", secondary=customer_group_links)


class CustomerGroup(Base):
    __tablename__ = "customer_group"
    id = Column(types.Integer, primary_key=True)
    internal_id = Column(types.String(32), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)
    customers = orm.relationship(Customer)


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    op.alter_column("customer", "customer_group_id", nullable=True, existing_type=mysql.INTEGER)
    op.drop_constraint("customer_group_ibfk_1", table_name="customer", type_="foreignkey")
    op.create_table(
        "customer_group_links",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("customer_group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ("customer_id",),
            ["customer.id"],
        ),
        sa.ForeignKeyConstraint(
            ("customer_group_id",),
            ["customer_group.id"],
        ),
        sa.UniqueConstraint("customer_id", "customer_group_id", name="_customer_custg_uc"),
    )

    for customer_group in session.query(CustomerGroup):
        print(f"Customer group {customer_group.internal_id}")
        print(f"customers {customer_group.customers}")
        if len(customer_group.customers) > 1:
            for customer in customer_group.customers:
                customer.customer_groups.append(customer_group)
        else:
            print(f"Deleting group {customer_group}")
            session.delete(customer_group)

    op.drop_column(
        table_name="customer",
        column_name="customer_group_id",
    )


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    op.add_column(
        "customer",
        sa.Column(
            name="customer_group_id",
            type_=mysql.INTEGER(display_width=11),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "customer_group_ibfk_1",
        source_table="customer_group",
        referent_table="customer",
        local_cols=["id"],
        remote_cols=["customer_group_id"],
    )
    for customer in session.query(Customer):
        if not Customer.customer_groups:
            customer_group = CustomerGroup(internal_id=customer.internal_id, name=customer.name)
            session.add(customer_group)
            session.commit()
            session.refresh(customer_group)
            customer.customer_group_id = customer_group.id
        else:
            customer.customer_group_id = customer.customer_groups[0].id
            print(
                f"Customer {customer.internal_id} is added to the group "
                f"{customer.customer_groups[0].name} "
            )
    op.drop_table("customer_group_links")
    session.commit()
