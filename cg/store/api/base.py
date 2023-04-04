"""All models aggregated in a base class"""
from typing import Type

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
    """All models in one base class."""

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
    def _get_query(table: Type[ModelBase]) -> Query:
        """Return a query for the given table."""
        return table.query

    def _get_outer_join_cases_with_analyses_query(self) -> Query:
        """Return a query for all cases in the database with an analysis."""
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

    def _get_join_cases_with_samples_query(self) -> Query:
        """Return a join query for all cases in the database with samples."""
        return self._get_query(table=Family).join(
            Family.links, FamilySample.sample, Family.customer
        )

    def _get_join_analysis_case_query(self) -> Query:
        """Return join analysis case query."""
        return self._get_query(table=Analysis).join(Analysis.family)

    def _get_join_case_sample_query(self) -> Query:
        """Return join case sample query."""
        return self._get_query(table=FamilySample).join(FamilySample.family, FamilySample.sample)

    def _get_join_sample_and_customer_query(self) -> Query:
        """Return join sample and customer query."""
        return self._get_query(table=Sample).join(Customer)

    def _get_join_flow_cell_sample_links_query(self) -> Query:
        """Return join flow cell samples and relationship query."""
        return self._get_query(table=Flowcell).join(Flowcell.samples, Sample.links)

    def _get_join_sample_family_query(self) -> Query:
        """Return a join sample case relationship query."""
        return self._get_query(table=Sample).join(Family.links, FamilySample.sample)

    def _get_join_sample_application_version_query(self) -> Query:
        """Return join sample to application version query."""
        return self._get_query(table=Sample).join(
            Sample.application_version, ApplicationVersion.application
        )
