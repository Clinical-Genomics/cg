"""move_synopsis_to_case

Revision ID: fab30255b84f
Revises: 432379a1adfa
Create Date: 2021-02-17 17:43:47.102289

"""
from typing import List

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import declarative_base

from alembic import op

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "fab30255b84f"
down_revision = "432379a1adfa"
branch_labels = None
depends_on = None


class Family(Base):
    __tablename__ = "family"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), unique=True, nullable=False)
    name = sa.Column(sa.types.String(128), nullable=False)

    _cohorts = sa.Column(sa.types.Text)
    _synopsis = sa.Column(sa.types.Text)

    @property
    def cohorts(self) -> List[str]:
        """Return a list of cohorts."""
        return self._cohorts.split(",") if self._cohorts else []

    @cohorts.setter
    def cohorts(self, cohort_list: List[str]):
        self._cohorts = ",".join(cohort_list) if cohort_list else None

    @property
    def synopsis(self) -> List[str]:
        """Return a list of synopsis."""
        return self._synopsis.split(",") if self._synopsis else []

    @synopsis.setter
    def synopsis(self, synopsis_list: List[str]):
        self._synopsis = ",".join(synopsis_list) if synopsis_list else None


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

    _cohorts = sa.Column(sa.types.Text)
    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), nullable=False, unique=True)
    name = sa.Column(sa.types.String(128), nullable=False)
    _synopsis = sa.Column(sa.types.Text)

    @property
    def cohorts(self) -> List[str]:
        """Return a list of cohorts."""
        return self._cohorts.split(",") if self._cohorts else []

    @cohorts.setter
    def cohorts(self, cohort_list: List[str]):
        self._cohorts = ",".join(cohort_list) if cohort_list else None

    @property
    def synopsis(self) -> List[str]:
        """Return a list of synopsis."""
        return self._synopsis.split(",") if self._synopsis else []

    @synopsis.setter
    def synopsis(self, synopsis_list: List[str]):
        self._synopsis = ",".join(synopsis_list) if synopsis_list else None


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.add_column("family", sa.Column("_synopsis", sa.TEXT))
    op.add_column("family", sa.Column("_cohorts", sa.TEXT))

    # copy data from sample._synopsis to family._synopsis
    for sample in session.query(Sample).filter(Sample._synopsis.isnot(None)):
        for link in sample.links:
            link.family._synopsis = sample._synopsis
    for sample in session.query(Sample).filter(Sample._cohorts.isnot(None)):
        for link in sample.links:
            link.family._cohorts = sample._cohorts
    session.commit()

    op.drop_column("sample", "_synopsis")
    op.drop_column("sample", "_cohorts")


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.add_column("sample", sa.Column("_synopsis", sa.TEXT))
    op.add_column("sample", sa.Column("_cohorts", sa.TEXT))

    # copy data from family._synopsis to sample._synopsis
    for family in session.query(Family).filter(Family._synopsis.isnot(None)):
        for link in family.links:
            link.sample._synopsis = family._synopsis
    for family in session.query(Family).filter(Family._cohorts.isnot(None)):
        for link in family.links:
            link.sample._cohorts = family._cohorts
    session.commit()

    op.drop_column("family", "_synopsis")
    op.drop_column("family", "_cohorts")
