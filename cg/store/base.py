"""All models aggregated in a base class."""

from dataclasses import dataclass
from typing import Callable, Type

from sqlalchemy import and_, func
from sqlalchemy.orm import Query, Session

from cg.store.filters.status_case_filters import CaseFilter, apply_case_filter
from cg.store.filters.status_customer_filters import (
    CustomerFilter,
    apply_customer_filter,
)
from cg.store.filters.status_sample_filters import SampleFilter, apply_sample_filter
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    ApplicationVersion,
    Case,
    CaseSample,
    Customer,
    Flowcell,
)
from cg.store.models import Model as ModelBase
from cg.store.models import Sample
from cg.utils.date import get_date_days_ago


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

    def _get_join_case_and_sample_query(self) -> Query:
        """Return join case sample query."""
        return self._get_query(table=Case).join(Case.links).join(CaseSample.sample)

    def _get_join_sample_and_customer_query(self) -> Query:
        """Return join sample and customer query."""
        return self._get_query(table=Sample).join(Customer)

    def _get_join_flow_cell_sample_links_query(self) -> Query:
        """Return join flow cell samples and relationship query."""
        return self._get_query(table=Flowcell).join(Flowcell.samples).join(Sample.links)

    def _get_join_sample_family_query(self) -> Query:
        """Return a join sample case relationship query."""
        return self._get_query(table=Sample).join(Case.links).join(CaseSample.sample)

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

    def _get_filtered_case_query(
        self,
        case_action: str | None,
        customer_id: str,
        data_analysis: str,
        days: int,
        exclude_customer_id: bool,
        internal_id: str,
        name: str,
        priority: str,
        sample_id: str,
    ) -> Query:
        cases_query: Query = self._get_query(table=Case)
        filter_functions: list[Callable] = []

        filter_case_order_date = None
        if days != 0:
            filter_case_order_date = get_date_days_ago(days_ago=days)
            filter_functions.append(CaseFilter.FILTER_NEW_BY_ORDER_DATE)
        if case_action:
            filter_functions.append(CaseFilter.FILTER_BY_ACTION)
        if priority:
            filter_functions.append(CaseFilter.FILTER_BY_PRIORITY)
        if internal_id:
            filter_functions.append(CaseFilter.FILTER_BY_INTERNAL_ID_SEARCH)
        if name:
            filter_functions.append(CaseFilter.FILTER_BY_NAME_SEARCH)
        if data_analysis:
            filter_functions.append(CaseFilter.FILTER_BY_WORKFLOW_SEARCH)

        cases_query = apply_case_filter(
            cases=cases_query,
            filter_functions=filter_functions,
            action=case_action,
            internal_id_search=internal_id,
            name_search=name,
            order_date=filter_case_order_date,
            workflow_search=data_analysis,
            priority=priority,
        )

        # customer filters
        customer_filters: list[Callable] = []
        if customer_id or exclude_customer_id:
            cases_query = cases_query.join(Case.customer)

        if customer_id:
            customer_filters.append(CustomerFilter.FILTER_BY_INTERNAL_ID)

        if exclude_customer_id:
            customer_filters.append(CustomerFilter.EXCLUDE_INTERNAL_ID)

        cases_query = apply_customer_filter(
            customers=cases_query,
            filter_functions=customer_filters,
            customer_internal_id=customer_id,
            exclude_customer_internal_id=exclude_customer_id,
        )

        # sample filters
        if sample_id:
            cases_query = cases_query.join(Case.links).join(CaseSample.sample)
            cases_query = apply_sample_filter(
                samples=cases_query,
                filter_functions=[SampleFilter.FILTER_BY_INTERNAL_ID_PATTERN],
                internal_id_pattern=sample_id,
            )
        else:
            cases_query = cases_query.outerjoin(Case.links).outerjoin(CaseSample.sample)

        # other joins
        cases_query = (
            cases_query.outerjoin(Case.analyses)
            .outerjoin(Sample.invoice)
            .outerjoin(Sample.flowcells)
        )
        return cases_query

    def _get_join_application_limitations_query(self) -> Query:
        """Return a join query for all application limitations."""
        return self._get_query(table=ApplicationLimitations).join(
            ApplicationLimitations.application
        )
