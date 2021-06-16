"""petname avatar

Revision ID: 7e344b9438bf
Revises: ed0be7286cee
Create Date: 2021-04-08 08:04:11.763421

"""
import random
from datetime import datetime
from time import sleep

from alembic import op
import sqlalchemy as sa
from cg.apps.avatar.api import Avatar
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.

revision = "7e344b9438bf"
down_revision = "ed0be7286cee"
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

    for family in session.query(Family).order_by(Family.ordered_at.desc()):

        print(f"Processing family: {str(family)}")

        for cnt in range(random.randint(0, 10)):
            sleep(1)
            print(".", end="", flush=True)

        avatar_urls = Avatar.get_avatar_urls(family.internal_id)
        for avatar_url in avatar_urls:
            if (
                avatar_url
                and find_family_by_avatar_url(avatar_url=avatar_url, session=session) is None
            ):
                break
            else:
                print(f"{avatar_url} already used - trying another url")

        family.avatar_url = avatar_url
        print(f"Altered family: {str(family)}")

        session.commit()


def downgrade():
    op.drop_column("family", "avatar_url")
