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
