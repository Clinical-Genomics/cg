"""Add name for invoice contact

Revision ID: ef472ce31931
Revises: 49ded71bd1a1
Create Date: 2021-05-03 09:21:58.047779

"""
from alembic import op
from sqlalchemy import (
    types,
    Column,
    orm,
    String,
)
from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.
revision = "ef472ce31931"
down_revision = "49ded71bd1a1"
branch_labels = None
depends_on = None

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customer"
    id = Column(types.Integer, primary_key=True)

    delivery_contact_email = Column(types.String(128))
    invoice_contact_email = Column(types.String(128))
    primary_contact_email = Column(types.String(128))

    # post-migration fields
    delivery_contact_name = Column(types.String(128))
    invoice_contact_name = Column(types.String(128))
    primary_contact_name = Column(types.String(128))


class User(Base):
    __tablename__ = "user"
    id = Column(types.Integer, primary_key=True)
    email = Column(types.String(128), unique=True, nullable=False)
    name = Column(types.String(128), nullable=False)


def upgrade():
    op.add_column("customer", Column("delivery_contact_name", String(128), nullable=True))
    op.add_column("customer", Column("invoice_contact_name", String(128), nullable=True))
    op.add_column("customer", Column("primary_contact_name", String(128), nullable=True))

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    # replace connection between customer and user with that users name
    count = 0
    for customer in session.query(Customer):
        if customer.delivery_contact_email:
            for user in session.query(User).filter(User.email == customer.delivery_contact_email):
                customer.delivery_contact_name = user.name
                print(
                    f"setting {user.name} to customer.delivery_contact_name for customer {customer.id} "
                )
                count += 1

        if customer.invoice_contact_email:
            for user in session.query(User).filter(User.email == customer.invoice_contact_email):
                customer.invoice_contact_name = user.name
                print(
                    f"setting {user.name} to customer.invoice_contact_name for customer {customer.id} "
                )
                count += 1
        if customer.primary_contact_email:
            for user in session.query(User).filter(User.email == customer.primary_contact_email):
                customer.primary_contact_name = user.name
                print(
                    f"setting {user.name} to customer.primary_contact_name for customer {customer.id} "
                )
                count += 1

    session.commit()
    print(f"Changed {count} names")


def downgrade():
    op.drop_column("customer", "delivery_contact_name")
    op.drop_column("customer", "invoice_contact_name")
    op.drop_column("customer", "primary_contact_name")
