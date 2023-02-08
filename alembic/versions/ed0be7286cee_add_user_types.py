"""Add user types

Revision ID: ed0be7286cee
Revises: ef472ce31931
Create Date: 2021-05-03 13:27:48.441597

"""
from alembic import op
from sqlalchemy import (
    types,
    Column,
    ForeignKey,
    orm,
    String,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.
revision = "ed0be7286cee"
down_revision = "ef472ce31931"
branch_labels = None
depends_on = None

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customer"
    id = Column(types.Integer, primary_key=True)

    # pre-migration fields
    delivery_contact_email = Column(types.String(128))
    invoice_contact_email = Column(types.String(128))
    primary_contact_email = Column(types.String(128))
    delivery_contact_name = Column(types.String(128))
    invoice_contact_name = Column(types.String(128))
    primary_contact_name = Column(types.String(128))

    # post-migration fields
    delivery_contact_id = Column(ForeignKey("user.id"))
    delivery_contact = orm.relationship("User", foreign_keys=[delivery_contact_id])
    invoice_contact_id = Column(ForeignKey("user.id"))
    invoice_contact = orm.relationship("User", foreign_keys=[invoice_contact_id])
    primary_contact_id = Column(ForeignKey("user.id"))
    primary_contact = orm.relationship("User", foreign_keys=[primary_contact_id])


class User(Base):
    __tablename__ = "user"
    id = Column(types.Integer, primary_key=True)
    email = Column(types.String(128), unique=True, nullable=False)
    name = Column(types.String(128))

    # post-migration fields
    order_portal_login = Column(types.Boolean, default=False)


def upgrade():
    op.add_column("user", Column("order_portal_login", mysql.BOOLEAN, default=False))

    op.add_column(
        "customer",
        Column("delivery_contact_id", mysql.INTEGER(display_width=11), autoincrement=False),
    )
    op.add_column(
        "customer",
        Column("invoice_contact_id", mysql.INTEGER(display_width=11), autoincrement=False),
    )
    op.add_column(
        "customer",
        Column("primary_contact_id", mysql.INTEGER(display_width=11), autoincrement=False),
    )

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    count = 0
    # replace email addresses on customers with connection between customer and user using users email
    for customer in session.query(Customer):
        if customer.delivery_contact_email:
            user = session.query(User).filter(User.email == customer.delivery_contact_email).first()
            if user:
                customer.delivery_contact_id = user.id
                print(
                    f"connecting user {user.id} directly to customer {customer.id} as delivery_contact"
                )
                count += 1
            else:
                print(
                    f"WARNING: could not find any user with email {customer.delivery_contact_email} to connect customer {customer.id} as delivery_contact"
                )

        if customer.invoice_contact_email:
            user = session.query(User).filter(User.email == customer.invoice_contact_email).first()
            if user:
                customer.invoice_contact_id = user.id
                print(
                    f"connecting user {user.id} directly to customer {customer.id} as invoice_contact"
                )
                count += 1
            else:
                print(
                    f"WARNING: could not find any user with email {customer.invoice_contact_email} to connect customer {customer.id} as invoice_contact"
                )

        if customer.primary_contact_email:
            user = session.query(User).filter(User.email == customer.primary_contact_email).first()
            if user:
                customer.primary_contact_id = user.id
                print(
                    f"connecting user {user.id} directly to customer {customer.id} as primary_contact"
                )
                count += 1
            else:
                print(
                    f"WARNING: could not find any user with email {customer.primary_contact_email} to connect customer {customer.id} as primary_contact"
                )

    session.commit()
    print(f"Changed {count} connections")

    count = 0
    for user in session.query(User):
        user.order_portal_login = True
        count += 1
    session.commit()
    print(f"Added {count} order portal logins")

    op.create_foreign_key(
        "delivery_contact_ibfk_1",
        "customer",
        "user",
        ["delivery_contact_id"],
        ["id"],
    )
    op.create_foreign_key(
        "invoice_contact_ibfk_1",
        "customer",
        "user",
        ["invoice_contact_id"],
        ["id"],
    )
    op.create_foreign_key(
        "primary_contact_ibfk_1",
        "customer",
        "user",
        ["primary_contact_id"],
        ["id"],
    )

    op.drop_column("customer", "delivery_contact_email")
    op.drop_column("customer", "invoice_contact_email")
    op.drop_column("customer", "primary_contact_email")
    op.drop_column("customer", "delivery_contact_name")
    op.drop_column("customer", "invoice_contact_name")
    op.drop_column("customer", "primary_contact_name")


def downgrade():
    op.add_column("customer", Column("delivery_contact_email", String(128), nullable=True))
    op.add_column("customer", Column("invoice_contact_email", String(128), nullable=True))
    op.add_column("customer", Column("primary_contact_email", String(128), nullable=True))
    op.add_column("customer", Column("delivery_contact_name", String(128), nullable=True))
    op.add_column("customer", Column("invoice_contact_name", String(128), nullable=True))
    op.add_column("customer", Column("primary_contact_name", String(128), nullable=True))

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    # replace connection between customer and user with that users email
    count = 0
    for customer in session.query(Customer):
        if customer.delivery_contact:
            customer.delivery_contact_email = customer.delivery_contact.email
            customer.delivery_contact_name = customer.delivery_contact.name
            print(
                f"setting {customer.delivery_contact.email} to customer.delivery_contact_email for customer {customer.id} "
            )
            count += 1
        if customer.invoice_contact:
            customer.invoice_contact_email = customer.invoice_contact.email
            customer.invoice_contact_name = customer.invoice_contact.name
            print(
                f"setting {customer.invoice_contact.email} to customer.invoice_contact_email for customer {customer.id} "
            )
            count += 1
        if customer.primary_contact:
            customer.primary_contact_email = customer.primary_contact.email
            customer.primary_contact_name = customer.primary_contact.name
            print(
                f"setting {customer.primary_contact.email} to customer.primary_contact_email for customer {customer.id} "
            )
            count += 1

    session.commit()
    print(f"Changed {count} connections")

    op.drop_constraint("delivery_contact_ibfk_1", "customer", type_="foreignkey")
    op.drop_column("customer", "delivery_contact_id")
    op.drop_constraint("invoice_contact_ibfk_1", "customer", type_="foreignkey")
    op.drop_column("customer", "invoice_contact_id")
    op.drop_constraint("primary_contact_ibfk_1", "customer", type_="foreignkey")
    op.drop_column("customer", "primary_contact_id")
    op.drop_column("user", "order_portal_login")
