"""Adds ticket to Families

Revision ID: 20750539a335
Revises: ddc94088be4d
Create Date: 2022-07-22 08:43:36.271777

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
from sqlalchemy.ext.declarative import declarative_base

revision = "20750539a335"
down_revision = "ddc94088be4d"
branch_labels = None
depends_on = None

Base = declarative_base()


class Family(Base):
    __tablename__ = "family"

    id = sa.Column(sa.types.Integer, primary_key=True)
    tickets = sa.Column(sa.types.String(32))


class FamilySample(Base):
    __tablename__ = "family_sample"

    id = sa.Column(sa.types.Integer, primary_key=True)
    family_id = sa.Column(sa.ForeignKey("family.id", ondelete="CASCADE"), nullable=False)
    sample_id = sa.Column(sa.ForeignKey("sample.id", ondelete="CASCADE"), nullable=False)

    family = sa.orm.relationship("Family", backref="links")
    sample = sa.orm.relationship("Sample", foreign_keys=[sample_id], backref="links")


class Sample(Base):
    __tablename__ = "sample"
    id = sa.Column(sa.types.Integer, primary_key=True)
    original_ticket = sa.Column(sa.types.String(32))


def upgrade():
    op.alter_column(
        "sample", "ticket_number", new_column_name="original_ticket", type_=mysql.VARCHAR(32)
    )
    op.add_column("family", sa.Column("tickets", type_=mysql.VARCHAR, nullable=True))
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for family in session.query(Family):
        if len(family.links) == 0:
            continue
        family.tickets = family.links[0].original_ticket
    session.commit()


def downgrade():
    op.alter_column(
        "sample", "original_ticket", new_column_name="ticket_number", type_=mysql.INTEGER
    )
    op.drop_column("family", "tickets")
