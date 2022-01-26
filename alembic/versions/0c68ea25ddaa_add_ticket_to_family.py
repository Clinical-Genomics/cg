"""Add ticket to family

Revision ID: 0c68ea25ddaa
Revises: c494649637d5
Create Date: 2021-12-21 11:24:44.554990

"""
import datetime
import random
from datetime import timedelta
from typing import List

from alembic import op
import sqlalchemy as sa

from sqlalchemy import orm, Column, types
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "0c68ea25ddaa"
down_revision = "f2edbd530656"
branch_labels = None
depends_on = None


class Family(Base):
    __tablename__ = "family"

    created_at = Column(types.DateTime)
    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), unique=True, nullable=False)
    name = sa.Column(sa.types.String(128), nullable=False)

    ticket_number = sa.Column(sa.types.Integer)


class FamilySample(Base):
    __tablename__ = "family_sample"
    __table_args__ = (sa.UniqueConstraint("family_id", "sample_id", name="_family_sample_uc"),)

    id = sa.Column(sa.types.Integer, primary_key=True)
    family_id = sa.Column(sa.ForeignKey("family.id", ondelete="CASCADE"), nullable=False)
    sample_id = sa.Column(sa.ForeignKey("sample.id", ondelete="CASCADE"), nullable=False)

    mother_id = sa.Column(sa.ForeignKey("sample.id"))
    father_id = sa.Column(sa.ForeignKey("sample.id"))

    family = orm.relationship("Family", backref="links")
    sample = orm.relationship("Sample", foreign_keys=[sample_id], backref="links")
    mother = orm.relationship("Sample", foreign_keys=[mother_id], backref="mother_links")
    father = orm.relationship("Sample", foreign_keys=[father_id], backref="father_links")


class Sample(Base):
    __tablename__ = "sample"

    created_at = Column(types.DateTime)
    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), nullable=False, unique=True)
    name = sa.Column(sa.types.String(128), nullable=False)
    ticket_number = sa.Column(sa.types.Integer)


def upgrade():

    print("adding ticket column to family", flush=True)
    op.add_column("family", Column("ticket_number", types.Integer, nullable=True))

    bind = op.get_bind()
    print(
        "Setting ticket number to all cases where we have a perfect order time match...", flush=True
    )
    bind.execute(
        "update family "
        "inner join family_sample as f_s on f_s.family_id = family.id  "
        "inner join sample as s on s.id = f_s.sample_id  "
        "set family.ticket_number = s.ticket_number "
        "where s.ordered_at = family.ordered_at;"
    )
    print(
        "Setting ticket number to all cases where ordered within 1 minute of the samples...",
        flush=True,
    )
    bind.execute(
        "update family "
        "inner join family_sample as f_s on f_s.family_id = family.id  "
        "inner join sample as s on s.id = f_s.sample_id  "
        "set family.ticket_number = s.ticket_number "
        " WHERE s.ordered_at > family.ordered_at - interval 1 minute and "
        "s.ordered_at < family.ordered_at + interval 1 minute;"
    )
    print("Done!")


def downgrade():
    op.drop_column("family", "ticket_number")
