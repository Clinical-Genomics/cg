"""Add table customer_user

Revision ID: 089edc289291
Revises: e9df15a35de4
Create Date: 2021-03-23 09:07:55.647204

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
from sqlalchemy.ext.declarative import declarative_base

revision = "089edc289291"
down_revision = "e9df15a35de4"
branch_labels = None
depends_on = None

Base = declarative_base()


customer_user = sa.Table(
    "customer_user",
    Base.metadata,
    sa.Column("customer_id", sa.types.Integer, sa.ForeignKey("customer.id"), nullable=False),
    sa.Column("user_id", sa.types.Integer, sa.ForeignKey("user.id"), nullable=False),
    sa.UniqueConstraint("customer_id", "user_id", name="_customer_user_uc"),
)


class Customer(Base):
    __tablename__ = "customer"
    id = sa.Column(sa.types.Integer, primary_key=True)

    users = sa.orm.relationship("User", secondary="customer_user", backref="customers")


class User(Base):
    __tablename__ = "user"
    id = sa.Column(sa.types.Integer, primary_key=True)

    customer_id = sa.Column(
        sa.ForeignKey("customer.id", ondelete="CASCADE", use_alter=True), nullable=False
    )
    customer = sa.orm.relationship("Customer", foreign_keys=[customer_id])


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    op.create_table(
        "customer_user",
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customer.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.UniqueConstraint("customer_id", "user_id", name="_customer_user_uc"),
    )

    # Change direct connection user->customer into user<-user_customer->customer
    for user in session.query(User):
        user.customer.users.append(user)
        print(f"connecting user {user.id} to customer {user.customer.id} ")

    session.commit()

    op.drop_constraint("user_ibfk_1", "user", type_="foreignkey")
    op.drop_column("user", "customer_id")


def downgrade():
    op.add_column(
        "user",
        sa.Column(
            "customer_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=False
        ),
    )

    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    # Change user<-user_customer->customer into direct connection user->customer
    for customer in session.query(Customer):
        for user in customer.users:
            user.customer = customer
            print(f"connecting user {user.id} directly to customer {user.customer.id} ")

    session.commit()

    op.create_foreign_key(
        "user_ibfk_1", "user", "customer", ["customer_id"], ["id"], ondelete="CASCADE"
    )

    op.drop_table("customer_user")
