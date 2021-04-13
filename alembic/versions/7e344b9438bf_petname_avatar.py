"""petname avatar

Revision ID: 7e344b9438bf
Revises: 089edc289291
Create Date: 2021-04-08 08:04:11.763421

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from cg.apps.avatar.api import Avatar
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.

revision = "7e344b9438bf"
down_revision = "089edc289291"
branch_labels = None
depends_on = None

Base = declarative_base()


class Family(Base):
    __tablename__ = "family"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), unique=True, nullable=False)
    name = sa.Column(sa.types.String(128), nullable=False)
    avatar_url = sa.Column(sa.types.TEXT)
    ordered_at = sa.Column(sa.types.DateTime, default=datetime.now)

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name}) {self.avatar_url or 'None'}"


def find_family_by_avatar_url(avatar_url, session):
    return session.query(Family).filter_by(avatar_url=avatar_url).first()


def upgrade():
    op.add_column("family", sa.Column("avatar_url", sa.TEXT))

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    tries = 1
    for family in session.query(Family).order_by(Family.ordered_at.desc()):

        print(f"Processing family: {str(family)}")

        while tries < 100:
            avatar_url = Avatar.get_avatar_url(family.internal_id, tries)
            if find_family_by_avatar_url(avatar_url=avatar_url, session=session) is None:
                break
            else:
                print(f"{avatar_url} already used - trying another url")
            tries += 2
        if tries > 1:
            tries -= 1
        family.avatar_url = avatar_url
        print(f"Altered family: {str(family)}")

        session.commit()


def downgrade():
    op.drop_column("family", "avatar_url")
