"""uc_sex_and_phenotypestatus

Revision ID: dd2000bcc7ca
Revises: 18e3b2aba252
Create Date: 2024-05-23 14:34:20.911911

"""

import sqlalchemy as sa
from sqlalchemy import Column, types
from sqlalchemy.orm import DeclarativeBase

from alembic import op

# revision identifiers, used by Alembic.
revision = "dd2000bcc7ca"
down_revision = "18e3b2aba252"
branch_labels = None
depends_on = None


class Model(DeclarativeBase):
    pass


class CaseSample(Model):
    __tablename__ = "case_sample"
    status = Column(types.String(32), nullable=False)


class Sample(Model):
    __tablename__ = "sample"
    sex = Column(types.String(32), nullable=False)


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for sample in session.query(CaseSample):
        sample.status.upper()
    for sample in session.query(Sample):
        sample.sex.upper()
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    for sample in session.query(CaseSample):
        sample.status.lower()
    for sample in session.query(Sample):
        sample.sex.lower()
    session.commit()
