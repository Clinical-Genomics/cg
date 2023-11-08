"""petname avatar

Revision ID: 7e344b9438bf
Revises: ed0be7286cee
Create Date: 2021-04-08 08:04:11.763421

"""
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from alembic import op

# revision identifiers, used by Alembic.

revision = "7e344b9438bf"
down_revision = "ed0be7286cee"
branch_labels = None
depends_on = None

Base = declarative_base()


class Case(Base):
    __tablename__ = "family"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), unique=True, nullable=False)
    name = sa.Column(sa.types.String(128), nullable=False)
    avatar_url = sa.Column(sa.types.TEXT)
    ordered_at = sa.Column(sa.types.DateTime, default=datetime.now)

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name}) {self.avatar_url or 'None'}"


def find_family_by_avatar_url(avatar_url, session):
    return session.query(Case).filter_by(avatar_url=avatar_url).first()


def upgrade():
    op.add_column("family", sa.Column("avatar_url", sa.TEXT))


def downgrade():
    op.drop_column("family", "avatar_url")
