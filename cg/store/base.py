"""All models aggregated in a base class."""

from dataclasses import dataclass
from typing import Type

from sqlalchemy import and_, func
from sqlalchemy.orm import Query, Session

from cg.store.models import Analysis, Application, ApplicationLimitations, ApplicationVersion
from cg.store.models import Base as ModelBase
from cg.store.models import (
    Case,
    CaseSample,
    Customer,
    IlluminaFlowCell,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Sample,
)


@dataclass
class BaseHandler:
    """All queries in one base class."""

    def __init__(self, session: Session):
        self.session = session

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

    def _get_join_application_ordertype_query(self) -> Query:
        """Return join application to order type query."""
        return self._get_query(table=Application).join(Application.order_types)

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
