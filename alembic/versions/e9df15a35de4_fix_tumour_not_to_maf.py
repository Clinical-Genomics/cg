"""Fix tumour not to MAF

Revision ID: e9df15a35de4
Revises: 998be2e367cf
Create Date: 2021-03-24 07:50:31.774381

"""
from datetime import datetime
from typing import List

from alembic import op
import sqlalchemy as sa
from cg.constants import Pipeline, DataDelivery, PREP_CATEGORIES

from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = "e9df15a35de4"
down_revision = "998be2e367cf"
branch_labels = None
depends_on = None

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customer"

    id = sa.Column(sa.types.Integer, primary_key=True)


class Family(Base):
    __tablename__ = "family"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), unique=True, nullable=False)
    name = sa.Column(sa.types.String(128), nullable=False)
    customer_id = sa.Column(sa.ForeignKey("customer.id", ondelete="CASCADE"), nullable=False)
    customer = orm.relationship(Customer, foreign_keys=[customer_id])
    data_analysis = sa.Column(sa.types.Enum(*list(Pipeline)))
    data_delivery = sa.Column(sa.types.Enum(*list(DataDelivery)))
    priority = sa.Column(sa.types.Integer, default=1, nullable=False)
    _panels = sa.Column(sa.types.Text)
    ordered_at = sa.Column(sa.types.DateTime, default=datetime.now)

    @property
    def panels(self) -> List[str]:
        """Return a list of panels."""
        return self._panels.split(",") if self._panels else []

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"


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


class Application(Base):
    __tablename__ = "application"
    id = sa.Column(sa.types.Integer, primary_key=True)
    tag = sa.Column(sa.types.String(32), unique=True, nullable=False)
    prep_category = sa.Column(sa.types.Enum(*PREP_CATEGORIES), nullable=False)
    versions = orm.relationship(
        "ApplicationVersion", order_by="ApplicationVersion.version", backref="application"
    )


class ApplicationVersion(Base):
    __tablename__ = "application_version"

    id = sa.Column(sa.types.Integer, primary_key=True)
    version = sa.Column(sa.types.Integer, nullable=False)
    application_id = sa.Column(sa.ForeignKey(Application.id), nullable=False)


class Sample(Base):
    __tablename__ = "sample"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(sa.types.String(32), nullable=False, unique=True)
    name = sa.Column(sa.types.String(128), nullable=False)

    application_version_id = sa.Column(sa.ForeignKey("application_version.id"), nullable=False)
    application_version = orm.relationship(
        ApplicationVersion, foreign_keys=[application_version_id]
    )
    is_tumour = sa.Column(sa.types.Boolean, default=False)


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    count = 0
    # change records that should is tumour and should not be sent to MAF
    for family in (
        session.query(Family)
        .filter(Family.customer_id == 1)
        .filter(Family.data_delivery == DataDelivery.FASTQ)
        .filter(Family.data_analysis == Pipeline.MIP_DNA)
        .filter(Family.priority == "research")
    ):
        if len(family.links) > 1:
            print(f"skipping case that has more than one link: {family}")
            continue

        for link in family.links:
            sample = link.sample

            if not sample.is_tumour:
                continue

            if (
                sample.application_version.application.prep_category == "wgs"
                and sample.name == family.name
            ):
                print(f"changing data analysis from MIP to FASTQ for: {family}")
                family.data_analysis = Pipeline.FASTQ
                count += 1

    session.commit()
    print(f"changed {count} records")


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    count = 0
    for family in (
        session.query(Family)
        .filter(Family.customer_id == 1)
        .filter(Family.data_delivery == DataDelivery.FASTQ)
        .filter(Family.data_analysis == Pipeline.FASTQ)
        .filter(Family.priority == "research")
    ):
        if len(family.links) > 1:
            print(f"skipping case that has more than one link: {family}")
            continue

        for link in family.links:
            sample = link.sample

            if not sample.is_tumour:
                continue

            if (
                sample.application_version.application.prep_category == "wgs"
                and sample.name == family.name
            ):
                print(f"changing data analysis from FASTQ to MIP-DNA for: {family}")
                family.data_analysis = Pipeline.MIP_DNA
                count += 1

    session.commit()
    print(f"changed {count} records")
