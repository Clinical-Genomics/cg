"""Base class with basic database operations."""

from typing import Type

from sqlalchemy import Subquery, and_, func
from sqlalchemy.orm import Query

from cg.store.database import get_session
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    ApplicationVersion,
    Base,
    Case,
    CaseSample,
    Customer,
    IlluminaFlowCell,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Order,
    Sample,
)

ModelBase = Base


class BaseHandler:

    def __init__(self):
        self.session = get_session()

    def _get_query(self, table: Type[ModelBase]) -> Query:
        """Return a query for the given table."""
        return self.session.query(table)

    def _get_outer_join_cases_with_analyses_query(self) -> Query:
        """Return a query for all cases in the database with an analysis."""
        return (
            self._get_query(table=Case)
            .outerjoin(Analysis)
            .join(Case.links)
            .join(CaseSample.sample)
            .join(ApplicationVersion)
            .join(Application)
        )

    def _get_case_query_for_analysis_start(self) -> Query:
        """Return a query for all cases and joins them with their latest analysis, if present."""
        latest_analysis_subquery: Subquery = (
            self.session.query(
                Analysis.case_id, func.max(Analysis.created_at).label("latest_created_at")
            )
            .group_by(Analysis.case_id)
            .subquery()
        )

        cases_with_only_latest_analysis: Query = (
            self.session.query(Case)
            .outerjoin(latest_analysis_subquery, latest_analysis_subquery.c.case_id == Case.id)
            .outerjoin(
                Analysis,
                and_(
                    Analysis.case_id == Case.id,
                    Analysis.created_at == latest_analysis_subquery.c.latest_created_at,
                ),
            )
        )
        complete_query: Query = (
            cases_with_only_latest_analysis.join(Case.links)
            .join(CaseSample.sample)
            .join(ApplicationVersion)
            .join(Application)
        )
        return complete_query

    def _get_join_cases_with_samples_query(self) -> Query:
        """Return a join query for all cases in the database with samples."""
        return (
            self._get_query(table=Case).join(Case.links).join(CaseSample.sample).join(Case.customer)
        )

    def _get_join_analysis_case_query(self) -> Query:
        """Return join analysis case query."""
        return self._get_query(table=Analysis).join(Analysis.case)

    def _get_join_case_sample_query(self) -> Query:
        """Return join case sample query."""
        return self._get_query(table=CaseSample).join(CaseSample.case).join(CaseSample.sample)

    def _join_sample_and_case(self):
        return (
            self._get_query(Case)
            .join(CaseSample, Case.id == CaseSample.case_id)
            .join(Sample, CaseSample.sample_id == Sample.id)
        )

    def _get_join_case_and_sample_query(self) -> Query:
        """Return join case sample query."""
        return self._get_query(table=Case).join(Case.links).join(CaseSample.sample)

    def _get_join_sample_and_customer_query(self) -> Query:
        """Return join sample and customer query."""
        return self._get_query(table=Sample).join(Customer)

    def _get_join_sample_family_query(self) -> Query:
        """Return a join sample case relationship query."""
        return self._get_query(table=Sample).join(Case.links).join(CaseSample.sample)

    def _get_join_sample_case_order_query(self) -> Query:
        """Return a query joining sample, cases_sample, case and order. Selects from sample."""
        return (
            self._get_query(table=Sample).join(Case.links).join(CaseSample.sample).join(Case.orders)
        )

    def _get_join_order_case_query(self) -> Query:
        """Return a query joining sample, cases_sample, case and order. Selects from sample."""
        return self._get_query(table=Order).join(Order.cases)

    def _get_join_application_ordertype_query(self) -> Query:
        """Return join application to order type query."""
        return self._get_query(table=Application).join(Application.order_type_applications)

    def _get_join_sample_application_version_query(self) -> Query:
        """Return join sample to application version query."""
        return (
            self._get_query(table=Sample)
            .join(Sample.application_version)
            .join(ApplicationVersion.application)
        )

    def _get_join_analysis_sample_family_query(self) -> Query:
        """Return join analysis to sample to case query."""
        return self._get_query(table=Analysis).join(Case).join(Case.links).join(CaseSample.sample)

    def _get_subquery_with_latest_case_analysis_date(self) -> Query:
        """Return a subquery with the case internal id and the date of its latest analysis."""
        case_and_date: Query = (
            self._get_join_analysis_case_query()
            .group_by(Case.id)
            .with_entities(Analysis.case_id, func.max(Analysis.started_at).label("started_at"))
            .subquery()
        )
        return case_and_date

    def _get_latest_analyses_for_cases_query(self) -> Query:
        """Return a join query for the latest analysis for each case."""
        analyses: Query = self._get_query(table=Analysis)
        case_and_date_subquery: Query = self._get_subquery_with_latest_case_analysis_date()
        return analyses.join(
            case_and_date_subquery,
            and_(
                Analysis.case_id == case_and_date_subquery.c.case_id,
                Analysis.started_at == case_and_date_subquery.c.started_at,
            ),
        )

    def _get_join_application_limitations_query(self) -> Query:
        """Return a join query for all application limitations."""
        return self._get_query(table=ApplicationLimitations).join(
            ApplicationLimitations.application
        )

    def _get_joined_illumina_sample_tables(self) -> Query:
        """Return a join query for all Illumina tables and Sample."""
        return (
            self._get_query(table=IlluminaSampleSequencingMetrics)
            .join(Sample)
            .join(IlluminaSequencingRun)
            .join(IlluminaFlowCell)
        )

    def commit_to_store(self):
        """Commit pending changes to the store."""
        self.session.commit()

    def add_item_to_store(self, item: ModelBase):
        """Add an item to the store in the current transaction."""
        self.session.add(item)

    def add_multiple_items_to_store(self, items: list[ModelBase]):
        """Add multiple items to the store in the current transaction."""
        self.session.add_all(items)

    def delete_item_from_store(self, item: ModelBase):
        """Delete an item from the store in the current transaction."""
        self.session.delete(item)

    def no_autoflush_context(self):
        """Return a context manager that disables autoflush for the session."""
        return self.session.no_autoflush

    def rollback(self):
        """Rollback any pending change to the store."""
        self.session.rollback()
