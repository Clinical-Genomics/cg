"""All models aggregated in a base class"""
from typing import Callable, Optional, Type, List

from sqlalchemy.orm import Query, Session
from sqlalchemy import and_, func
from dataclasses import dataclass
from cg.store.filters.status_case_filters import CaseFilter, apply_case_filter
from cg.store.filters.status_customer_filters import CustomerFilter, apply_customer_filter
from cg.store.filters.status_sample_filters import SampleFilter, apply_sample_filter
from cg.store.models import (
    Analysis,
    Application,
    ApplicationVersion,
    Customer,
    Family,
    FamilySample,
    Flowcell,
    Sample,
)
from cg.utils.date import get_date_days_ago

from cg.store.models import Model as ModelBase


@dataclass
class BaseHandler:
    """All models in one base class."""

    def __init__(self, session: Session):
        self.session = session

    def _get_query(self, table: Type[ModelBase]) -> Query:
        """Return a query for the given table."""
        return self.session.query(table)

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

    def _get_join_case_and_sample_query(self) -> Query:
        """Return join case sample query."""
        return self._get_query(table=Family).join(Family.links, FamilySample.sample)

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

    def _get_join_analysis_sample_family_query(self) -> Query:
        """Return join analysis to sample to case query."""
        return self._get_query(table=Analysis).join(Family, Family.links, FamilySample.sample)

    def _get_subquery_with_latest_case_analysis_date(self) -> Query:
        """Return a subquery with the case internal id and the date of its latest analysis."""
        case_and_date: Query = (
            self._get_join_analysis_case_query()
            .group_by(Family.id)
            .with_entities(Analysis.family_id, func.max(Analysis.started_at).label("started_at"))
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
                Analysis.family_id == case_and_date_subquery.c.family_id,
                Analysis.started_at == case_and_date_subquery.c.started_at,
            ),
        )

    def _get_filtered_case_query(
        self,
        case_action: Optional[str],
        customer_id: str,
        data_analysis: str,
        days: int,
        exclude_customer_id: bool,
        internal_id: str,
        name: str,
        priority: str,
        sample_id: str,
    ) -> Query:
        cases_query: Query = self._get_query(table=Family)
        filter_functions: List[Callable] = []

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
            filter_functions.append(CaseFilter.FILTER_BY_PIPELINE_SEARCH)

        cases_query = apply_case_filter(
            cases=cases_query,
            filter_functions=filter_functions,
            order_date=filter_case_order_date,
            action=case_action,
            priority=priority,
            internal_id_search=internal_id,
            name_search=name,
            pipeline_search=data_analysis,
        )

        # customer filters
        customer_filters: List[Callable] = []
        if customer_id or exclude_customer_id:
            cases_query = cases_query.join(Family.customer)

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
            cases_query = cases_query.join(Family.links, FamilySample.sample)
            cases_query = apply_sample_filter(
                samples=cases_query,
                filter_functions=[SampleFilter.FILTER_BY_INTERNAL_ID_PATTERN],
                internal_id_pattern=sample_id,
            )
        else:
            cases_query = cases_query.outerjoin(Family.links, FamilySample.sample)

        # other joins
        cases_query = cases_query.outerjoin(Family.analyses, Sample.invoice, Sample.flowcells)
        return cases_query
