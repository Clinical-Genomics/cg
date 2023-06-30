from datetime import datetime
from typing import Optional, List, Callable
from enum import Enum
from cgmodels.cg.constants import Pipeline
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Query

from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY
from cg.constants.constants import CaseActions, DataDelivery
from cg.constants.observations import (
    LOQUSDB_SUPPORTED_PIPELINES,
    LOQUSDB_MIP_SEQUENCING_METHODS,
    LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
)
from cg.store.models import Analysis, Application, Customer, Family, Sample


def filter_cases_by_action(cases: Query, action: str, **kwargs) -> Query:
    """Filter cases with matching action."""
    return cases.filter(Family.action == action) if action else cases


def filter_cases_by_case_search(cases: Query, case_search: str, **kwargs) -> Query:
    """Filter cases with matching internal id or name."""
    return (
        cases.filter(
            or_(
                Family.internal_id.like(f"%{case_search}%"),
                Family.name.like(f"%{case_search}%"),
            )
        )
        if case_search
        else cases
    )


def filter_cases_by_customer_entry_id(cases: Query, customer_entry_id: int, **kwargs) -> Query:
    """Filter cases with matching customer id."""
    return cases.filter(Family.customer_id == customer_entry_id)


def filter_cases_by_customer_entry_ids(
    cases: Query, customer_entry_ids: List[int], **kwargs
) -> Query:
    """Filter cases with matching customer ids."""
    return cases.filter(Family.customer_id.in_(customer_entry_ids)) if customer_entry_ids else cases


def filter_cases_by_entry_id(cases: Query, entry_id: int, **kwargs) -> Query:
    """Filter cases by entry id."""
    return cases.filter(Family.id == entry_id)


def filter_case_by_internal_id(cases: Query, internal_id: str, **kwargs) -> Query:
    """Filter cases with matching internal id."""
    return cases.filter(Family.internal_id == internal_id)


def filter_cases_by_internal_id_search(cases: Query, internal_id_search: str, **kwargs) -> Query:
    """Filter cases with internal ids matching the search pattern."""
    return cases.filter(Family.internal_id.like(f"%{internal_id_search}%"))


def filter_cases_by_name(cases: Query, name: str, **kwargs) -> Query:
    """Filter cases with matching name."""
    return cases.filter(Family.name == name) if name else cases


def filter_cases_by_name_search(cases: Query, name_search: str, **kwargs) -> Query:
    """Filter cases with names matching the search pattern."""
    return cases.filter(Family.name.like(f"%{name_search}%"))


def filter_cases_by_pipeline_search(cases: Query, pipeline_search: str, **kwargs) -> Query:
    """Filter cases with pipeline search pattern."""
    return cases.filter(Family.data_analysis.ilike(f"%{pipeline_search}%"))


def filter_cases_by_priority(cases: Query, priority: str, **kwargs) -> Query:
    """Filter cases with matching priority."""
    return cases.filter(Family.priority == priority)


def filter_cases_by_ticket_id(cases: Query, ticket_id: str, **kwargs) -> Query:
    """Filter cases with matching ticket id."""
    return cases.filter(Family.tickets.contains(ticket_id))


def filter_cases_for_analysis(cases: Query, **kwargs) -> Query:
    """Filter cases in need of analysis by:
    1. Action set to analyze or
    2. Internally created cases with no action set and no prior analysis or
    3. Cases with no action, but new sequence data
    """
    return cases.filter(
        or_(
            Family.action == CaseActions.ANALYZE,
            and_(
                Application.is_external.isnot(True),
                Family.action.is_(None),
                Analysis.created_at.is_(None),
            ),
            and_(
                Family.action.is_(None),
                Analysis.created_at < Sample.sequenced_at,
            ),
        )
    )


def filter_cases_has_sequence(cases: Query, **kwargs) -> Query:
    """Filter cases that is not sequenced according to record in StatusDB."""
    return cases.filter(or_(Application.is_external, Sample.sequenced_at.isnot(None)))


def filter_cases_not_analysed(cases: Query, **kwargs) -> Query:
    """Filter cases that have not been analysed and are not currently being analysed."""
    not_analyzed_condition = not_(Family.analyses.any(Analysis.completed_at.isnot(None)))
    not_in_progress_condition = Family.action != CaseActions.ANALYZE

    return cases.filter(and_(not_analyzed_condition, not_in_progress_condition))


def filter_cases_with_pipeline(cases: Query, pipeline: Pipeline = None, **kwargs) -> Query:
    """Filter cases with pipeline."""
    return cases.filter(Family.data_analysis == pipeline) if pipeline else cases


def filter_cases_with_loqusdb_supported_pipeline(
    cases: Query, pipeline: Pipeline = None, **kwargs
) -> Query:
    """Filter Loqusdb related cases with pipeline."""
    records: Query = (
        cases.filter(Family.data_analysis == pipeline)
        if pipeline
        else cases.filter(Family.data_analysis.in_(LOQUSDB_SUPPORTED_PIPELINES))
    )
    return records.filter(Customer.loqus_upload == True)


def filter_cases_with_loqusdb_supported_sequencing_method(
    cases: Query, pipeline: Pipeline = None, **kwargs
) -> Query:
    """Filter cases with Loqusdb supported sequencing method."""
    supported_sequencing_methods = {
        Pipeline.MIP_DNA: LOQUSDB_MIP_SEQUENCING_METHODS,
        Pipeline.BALSAMIC: LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
    }
    return (
        cases.filter(Application.prep_category.in_(supported_sequencing_methods[pipeline]))
        if pipeline
        else cases
    )


def filter_cases_with_scout_data_delivery(cases: Query, **kwargs) -> Query:
    """Filter cases containing Scout as a data delivery option."""
    return cases.filter(Family.data_delivery.contains(DataDelivery.SCOUT))


def filter_newer_cases_by_order_date(cases: Query, order_date: datetime, **kwargs) -> Query:
    """Filter cases newer than date."""
    cases: Query = cases.filter(Family.ordered_at > order_date)
    return cases.order_by(Family.ordered_at.asc())


def filter_inactive_analysis_cases(cases: Query, **kwargs) -> Query:
    """Filter cases which are not set or on hold."""
    return cases.filter(
        or_(
            Family.action.is_(None),
            Family.action == CaseActions.HOLD,
        )
    )


def filter_older_cases_by_creation_date(cases: Query, creation_date: datetime, **kwargs) -> Query:
    """Filter older cases compared to date."""
    cases = cases.filter(Family.created_at < creation_date)
    return cases.order_by(Family.created_at.asc())


def filter_report_supported_data_delivery_cases(cases: Query, **kwargs) -> Query:
    """Filter cases with a valid data delivery for delivery report generation."""
    return cases.filter(Family.data_delivery.in_(REPORT_SUPPORTED_DATA_DELIVERY))


def filter_running_cases(cases: Query, **kwargs) -> Query:
    """Filter cases which are running."""
    return cases.filter(Family.action == CaseActions.RUNNING)


def order_cases_by_created_at(cases: Query, **kwargs) -> Query:
    """Order cases by created at."""
    return cases.order_by(Family.created_at.desc())


def apply_case_filter(
    cases: Query,
    filter_functions: List[Callable],
    action: Optional[str] = None,
    case_search: Optional[str] = None,
    creation_date: Optional[datetime] = None,
    customer_entry_id: Optional[int] = None,
    customer_entry_ids: Optional[List[int]] = None,
    entry_id: Optional[int] = None,
    internal_id: Optional[str] = None,
    internal_id_search: Optional[str] = None,
    name: Optional[str] = None,
    name_search: Optional[str] = None,
    order_date: Optional[datetime] = None,
    pipeline: Optional[Pipeline] = None,
    pipeline_search: Optional[str] = None,
    priority: Optional[str] = None,
    ticket_id: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        cases: Query = function(
            action=action,
            case_search=case_search,
            cases=cases,
            creation_date=creation_date,
            customer_entry_id=customer_entry_id,
            customer_entry_ids=customer_entry_ids,
            entry_id=entry_id,
            internal_id=internal_id,
            internal_id_search=internal_id_search,
            name=name,
            name_search=name_search,
            order_date=order_date,
            pipeline=pipeline,
            pipeline_search=pipeline_search,
            priority=priority,
            ticket_id=ticket_id,
        )
    return cases


class CaseFilter(Enum):
    """Define case filters."""

    FILTER_BY_ACTION: Callable = filter_cases_by_action
    FILTER_BY_CASE_SEARCH: Callable = filter_cases_by_case_search
    FILTER_BY_CUSTOMER_ENTRY_ID: Callable = filter_cases_by_customer_entry_id
    FILTER_BY_CUSTOMER_ENTRY_IDS: Callable = filter_cases_by_customer_entry_ids
    FILTER_BY_ENTRY_ID: Callable = filter_cases_by_entry_id
    FILTER_BY_INTERNAL_ID: Callable = filter_case_by_internal_id
    FILTER_BY_INTERNAL_ID_SEARCH: Callable = filter_cases_by_internal_id_search
    FILTER_BY_NAME: Callable = filter_cases_by_name
    FILTER_BY_NAME_SEARCH: Callable = filter_cases_by_name_search
    FILTER_BY_PIPELINE_SEARCH: Callable = filter_cases_by_pipeline_search
    FILTER_BY_PRIORITY: Callable = filter_cases_by_priority
    FILTER_BY_TICKET: Callable = filter_cases_by_ticket_id
    FILTER_FOR_ANALYSIS: Callable = filter_cases_for_analysis
    FILTER_HAS_INACTIVE_ANALYSIS: Callable = filter_inactive_analysis_cases
    FILTER_HAS_SEQUENCE: Callable = filter_cases_has_sequence
    FILTER_IS_RUNNING: Callable = filter_running_cases
    FILTER_NEW_BY_ORDER_DATE: Callable = filter_newer_cases_by_order_date
    FILTER_NOT_ANALYSED: Callable = filter_cases_not_analysed
    FILTER_OLD_BY_CREATION_DATE: Callable = filter_older_cases_by_creation_date
    FILTER_REPORT_SUPPORTED: Callable = filter_report_supported_data_delivery_cases
    FILTER_WITH_LOQUSDB_SUPPORTED_PIPELINE: Callable = filter_cases_with_loqusdb_supported_pipeline
    FILTER_WITH_LOQUSDB_SUPPORTED_SEQUENCING_METHOD: Callable = (
        filter_cases_with_loqusdb_supported_sequencing_method
    )
    FILTER_WITH_PIPELINE: Callable = filter_cases_with_pipeline
    FILTER_WITH_SCOUT_DELIVERY: Callable = filter_cases_with_scout_data_delivery
    ORDER_BY_CREATED_AT: Callable = order_cases_by_created_at
