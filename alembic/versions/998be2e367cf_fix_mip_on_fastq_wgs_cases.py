"""fix-mip-on-fastq-wgs-cases

Revision ID: 998be2e367cf
Revises: fab30255b84f
Create Date: 2021-02-26 10:03:23.560737

"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import declarative_base

from alembic import op
from cg.constants import (
    PREP_CATEGORIES,
    DataDelivery,
    Workflow,
)

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "998be2e367cf"
down_revision = "fab30255b84f"
branch_labels = None
depends_on = None


class Customer(Base):
    __tablename__ = "customer"

    id = sa.Column(sa.types.Integer, primary_key=True)


class Case(Base):
    __tablename__ = "family"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(
        sa.types.String(32),
        unique=True,
        nullable=False,
    )
    name = sa.Column(sa.types.String(128), nullable=False)
    customer_id = sa.Column(
        sa.ForeignKey("customer.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer = orm.relationship(Customer, foreign_keys=[customer_id])
    data_analysis = sa.Column(sa.types.Enum(*list(Workflow)))
    data_delivery = sa.Column(sa.types.Enum(*list(DataDelivery)))
    priority = sa.Column(
        sa.types.Integer,
        default=1,
        nullable=False,
    )
    _panels = sa.Column(sa.types.Text)
    ordered_at = sa.Column(sa.types.DateTime, default=datetime.now)

    @property
    def panels(self) -> list[str]:
        """Return a list of panels."""
        return self._panels.split(",") if self._panels else []

    def __str__(self) -> str:
        return f"{self.internal_id} ({self.name})"


class FamilySample(Base):
    __tablename__ = "family_sample"
    __table_args__ = (
        sa.UniqueConstraint(
            "family_id",
            "sample_id",
            name="_family_sample_uc",
        ),
    )

    id = sa.Column(sa.types.Integer, primary_key=True)
    family_id = sa.Column(
        sa.ForeignKey("family.id", ondelete="CASCADE"),
        nullable=False,
    )
    sample_id = sa.Column(
        sa.ForeignKey("sample.id", ondelete="CASCADE"),
        nullable=False,
    )

    mother_id = sa.Column(sa.ForeignKey("sample.id"))
    father_id = sa.Column(sa.ForeignKey("sample.id"))

    family = orm.relationship("Case", backref="links")
    sample = orm.relationship(
        "Sample",
        foreign_keys=[sample_id],
        backref="links",
    )
    mother = orm.relationship(
        "Sample",
        foreign_keys=[mother_id],
        backref="mother_links",
    )
    father = orm.relationship(
        "Sample",
        foreign_keys=[father_id],
        backref="father_links",
    )


class Application(Base):
    __tablename__ = "application"
    id = sa.Column(sa.types.Integer, primary_key=True)
    tag = sa.Column(
        sa.types.String(32),
        unique=True,
        nullable=False,
    )
    prep_category = sa.Column(
        sa.types.Enum(*PREP_CATEGORIES),
        nullable=False,
    )
    versions = orm.relationship(
        "ApplicationVersion",
        order_by="ApplicationVersion.version",
        backref="application",
    )


class ApplicationVersion(Base):
    __tablename__ = "application_version"

    id = sa.Column(sa.types.Integer, primary_key=True)
    version = sa.Column(sa.types.Integer, nullable=False)
    application_id = sa.Column(
        sa.ForeignKey(Application.id),
        nullable=False,
    )


class Sample(Base):
    __tablename__ = "sample"

    id = sa.Column(sa.types.Integer, primary_key=True)
    internal_id = sa.Column(
        sa.types.String(32),
        nullable=False,
        unique=True,
    )
    name = sa.Column(sa.types.String(128), nullable=False)

    application_version_id = sa.Column(
        sa.ForeignKey("application_version.id"),
        nullable=False,
    )
    application_version = orm.relationship(
        ApplicationVersion,
        foreign_keys=[application_version_id],
    )


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    count = 0
    # change records that should have been run with MIP for MAF
    for family in (
        session.query(Case)
        .filter(Case.customer_id == 1)
        .filter(Case.data_delivery == DataDelivery.FASTQ)
        .filter(Case.data_analysis == Workflow.FASTQ)
        .filter(Case.priority == "research")
        .filter(Case.ordered_at >= datetime(year=2021, month=2, day=2))
    ):
        if len(family.links) > 1:
            print(f"skipping case that has more than one link: {family}")
            continue

        for link in family.links:
            sample = link.sample
            if (
                sample.application_version.application.prep_category == "wgs"
                and sample.name == family.name
            ):
                print(f"changing data analysis from FASTQ to MIP for: {family}")
                family.data_analysis = Workflow.MIP_DNA
                count += 1

    session.commit()

    print(f"changed {count} records")


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    count = 0
    for family in (
        session.query(Case)
        .filter(Case.customer_id == 1)
        .filter(Case.data_delivery == DataDelivery.FASTQ)
        .filter(Case.data_analysis == Workflow.MIP_DNA)
        .filter(Case.priority == "research")
        .filter(Case.ordered_at >= datetime(year=2021, month=2, day=2))
    ):
        if len(family.links) > 1:
            print(f"skipping case that has more than one link: {family}")
            continue

        for link in family.links:
            sample = link.sample
            if (
                sample.application_version.application.prep_category == "wgs"
                and sample.name == family.name
            ):
                print(f"changing data analysis from MIP to FASTQ for: {family}")
                family.data_analysis = Workflow.FASTQ
                count += 1

    session.commit()
    print(f"changed {count} records")
