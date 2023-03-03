"""All models aggregated in a base class"""
from alchy import Query
from attr import dataclass

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
    Model,
    Organism,
    Panel,
    Pool,
    Sample,
    User,
)


@dataclass
class BaseHandler:
    """All models in one base class"""

    Analysis = Analysis
    Application = Application
    ApplicationVersion = ApplicationVersion
    Bed = Bed
    BedVersion = BedVersion
    Collaboration = Collaboration
    Customer = Customer
    Delivery = Delivery
    Family = Family
    FamilySample = FamilySample
    Flowcell = Flowcell
    Invoice = Invoice
    Organism = Organism
    Panel = Panel
    Pool = Pool
    Sample = Sample
    User = User

    @staticmethod
    def _get_query(table: Model):
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
