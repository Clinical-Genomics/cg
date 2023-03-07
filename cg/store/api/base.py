"""All models aggregated in a base class"""
from typing import Any, Type

from alchy import Query, ModelBase
from dataclasses import dataclass

from cg.store.models import (
    Analysis,
    Application,
    ApplicationVersion,
    Bed,
    BedVersion,
    Collaboration,
    Customer,
    Delivery,
    Family,
    FamilySample,
    Flowcell,
    Invoice,
    Organism,
    Panel,
    Pool,
    Sample,
    User,
)


@dataclass
class BaseHandler:
    """All models in one base class"""

    Analysis: Type[ModelBase] = Analysis
    Application: Type[ModelBase] = Application
    ApplicationVersion: Type[ModelBase] = ApplicationVersion
    Bed: Type[ModelBase] = Bed
    BedVersion: Type[ModelBase] = BedVersion
    Collaboration: Type[ModelBase] = Collaboration
    Customer: Type[ModelBase] = Customer
    Delivery: Type[ModelBase] = Delivery
    Family: Type[ModelBase] = Family
    FamilySample: Type[ModelBase] = FamilySample
    Flowcell: Type[ModelBase] = Flowcell
    Invoice: Type[ModelBase] = Invoice
    Organism: Type[ModelBase] = Organism
    Panel: Type[ModelBase] = Panel
    Pool: Type[ModelBase] = Pool
    Sample: Type[ModelBase] = Sample
    User: Type[ModelBase] = User

    @staticmethod
    def _get_query(table: Any) -> Query:
        return table.query

    def samples_to_receive(self, external=False) -> Query:
        """Fetch incoming samples."""
        return (
            self._get_query(table=Sample)
            .join(
                Sample.application_version,
                ApplicationVersion.application,
            )
            .filter(
                Sample.received_at.is_(None),
                Sample.downsampled_to.is_(None),
                Application.is_external == external,
            )
            .order_by(Sample.ordered_at)
        )

    def samples_to_prepare(self) -> Query:
        """Fetch samples in lab prep queue."""
        return (
            self._get_query(table=Sample)
            .join(
                Sample.application_version,
                ApplicationVersion.application,
            )
            .filter(
                Sample.received_at.isnot(None),
                Sample.prepared_at.is_(None),
                Sample.downsampled_to.is_(None),
                Application.is_external == False,
                Sample.sequenced_at.is_(None),
            )
            .order_by(Sample.received_at)
        )

    def samples_to_sequence(self) -> Query:
        """Fetch samples in sequencing."""
        return (
            self._get_query(table=Sample)
            .join(
                Sample.application_version,
                ApplicationVersion.application,
            )
            .filter(
                Sample.prepared_at.isnot(None),
                Sample.sequenced_at.is_(None),
                Sample.downsampled_to.is_(None),
                Application.is_external == False,
            )
            .order_by(Sample.received_at)
        )

    def get_families_with_analyses(self) -> Query:
        """Return all cases in the database with an analysis."""
        return (
            self._get_query(table=Family)
            .outerjoin(Analysis)
            .join(
                Family.links,
                FamilySample.sample,
                ApplicationVersion,
                Application,
            )
        )

    def get_families_with_samples(self) -> Query:
        """Return all cases in the database with samples."""
        return self._get_query(table=Family).join(
            Family.links, FamilySample.sample, Family.customer
        )

    def _get_analysis_case_query(self) -> Query:
        """Return analysis query."""
        return self._get_query(table=Analysis).join(Analysis.family)

    def _get_case_sample_query(self) -> Query:
        """Return case sample query."""
        return self._get_query(table=FamilySample).join(FamilySample.family, FamilySample.sample)

    def _get_sample_case_query(self) -> Query:
        """Return a sample case relationship query."""
        return self.Sample.query.join(Family.links, FamilySample.sample)
