from datetime import datetime
from enum import Enum
from typing import Callable

from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Query

from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY
from cg.constants.constants import CaseActions, DataDelivery, SequencingQCStatus, Workflow
from cg.constants.observations import (
    LOQUSDB_CANCER_SEQUENCING_METHODS,
    LOQUSDB_RARE_DISEASE_SEQUENCING_METHODS,
    LOQUSDB_SUPPORTED_WORKFLOWS,
)
from cg.store.models import Analysis, Application, Case, Customer, Sample


def filter_cases_by_action(cases: Query, action: str, **kwargs) -> Query:
    """Filter cases with matching action."""
    return cases.filter(Case.action == action) if action else cases


def filter_cases_by_case_search(cases: Query, case_search: str, **kwargs) -> Query:
    """Filter cases with matching internal id or name."""
    return (
        cases.filter(
            or_(
                Case.internal_id.contains(case_search),
                Case.name.contains(case_search),
            )
        )
        if case_search
        else cases
    )


def filter_cases_by_customer_entry_id(cases: Query, customer_entry_id: int, **kwargs) -> Query:
    """Filter cases with matching customer id."""
    return cases.filter(Case.customer_id == customer_entry_id)


def filter_cases_by_customer_entry_ids(
    cases: Query, customer_entry_ids: list[int], **kwargs
) -> Query:
    """Filter cases with matching customer ids."""
    return cases.filter(Case.customer_id.in_(customer_entry_ids)) if customer_entry_ids else cases


def filter_cases_by_entry_id(cases: Query, entry_id: int, **kwargs) -> Query:
    """Filter cases by entry id."""
    return cases.filter(Case.id == entry_id)


def filter_case_by_internal_id(cases: Query, internal_id: str, **kwargs) -> Query:
    """Filter cases with matching internal id."""
    return cases.filter(Case.internal_id == internal_id)


def filter_cases_by_internal_ids(cases: Query, internal_ids: list[str], **kwargs) -> Query:
    """Filter cases with internal ids."""
    return cases.filter(Case.internal_id.in_(internal_ids))


def filter_cases_by_internal_id_search(cases: Query, internal_id_search: str, **kwargs) -> Query:
    """Filter cases with internal ids matching the search pattern."""
    return cases.filter(Case.internal_id.contains(internal_id_search))


def filter_cases_by_name(cases: Query, name: str, **kwargs) -> Query:
    """Filter cases with matching name."""
    return cases.filter(Case.name == name) if name else cases


def filter_cases_by_name_search(cases: Query, name_search: str, **kwargs) -> Query:
    """Filter cases with names matching the search pattern."""
    return cases.filter(Case.name.contains(name_search))


def filter_cases_by_workflows(cases: Query, workflows: list[Workflow], **kwargs) -> Query:
    """Filter cases by data analysis types."""
    return cases.filter(Case.data_analysis.in_(workflows))


def filter_cases_by_workflow_search(cases: Query, workflow_search: str, **kwargs) -> Query:
    """Filter cases with a workflow search pattern."""
    return cases.filter(Case.data_analysis.contains(workflow_search))


def filter_cases_by_priority(cases: Query, priority: str, **kwargs) -> Query:
    """Filter cases with matching priority."""
    return cases.filter(Case.priority == priority)


def filter_cases_for_analysis(cases: Query, **kwargs) -> Query:
    """Filter cases in need of analysis by:
    1. Action set to analyze or
    2. Internally created cases with no action set and no prior analysis or
    3. Cases with no action, but new sequence data
    """
    return cases.filter(
        or_(
            # Overriding state: Analyse no matter what
            Case.action == CaseActions.ANALYZE,
            # Case has not been analysed before
            and_(
                Application.is_external.isnot(True),
                Case.action.is_(None),
                Analysis.created_at.is_(None),
            ),
            # Case contains new data that has not been analysed. (Only relevant for microSALT)
            and_(
                Case.action.is_(None),
                Analysis.created_at < Sample.last_sequenced_at,
            ),
            # Cases manually set to top-up by production that get the new data
            and_(Case.action == CaseActions.TOP_UP, Analysis.created_at < Sample.last_sequenced_at),
        )
    )


def filter_cases_has_sequence(cases: Query, **kwargs) -> Query:
    """Filter cases that are not sequenced according to record in StatusDB."""
    return cases.filter(or_(Application.is_external, Sample.last_sequenced_at.isnot(None)))


def filter_cases_not_analysed(cases: Query, **kwargs) -> Query:
    """Filter cases that have not been analysed and are not currently being analysed."""
    not_analyzed_condition = not_(Case.analyses.any(Analysis.completed_at.isnot(None)))
    not_in_progress_condition = Case.action != CaseActions.ANALYZE

    return cases.filter(and_(not_analyzed_condition, not_in_progress_condition))


def filter_cases_with_workflow(cases: Query, workflow: Workflow = None, **kwargs) -> Query:
    """Filter cases with workflow."""
    return cases.filter(Case.data_analysis == workflow) if workflow else cases


def filter_cases_with_loqusdb_supported_workflow(
    cases: Query, workflow: Workflow = None, **kwargs
) -> Query:
    """Filter Loqusdb related cases with workflow."""
    records: Query = (
        cases.filter(Case.data_analysis == workflow)
        if workflow
        else cases.filter(Case.data_analysis.in_(LOQUSDB_SUPPORTED_WORKFLOWS))
    )
    return records.filter(Customer.loqus_upload == True)


def filter_cases_with_loqusdb_supported_sequencing_method(
    cases: Query, workflow: Workflow = None, **kwargs
) -> Query:
    """Filter cases with Loqusdb supported sequencing method."""
    supported_sequencing_methods = {
        Workflow.MIP_DNA: LOQUSDB_RARE_DISEASE_SEQUENCING_METHODS,
        Workflow.BALSAMIC: LOQUSDB_CANCER_SEQUENCING_METHODS,
    }
    return (
        cases.filter(Application.prep_category.in_(supported_sequencing_methods[workflow]))
        if workflow
        else cases
    )


def filter_cases_with_scout_data_delivery(cases: Query, **kwargs) -> Query:
    """Filter cases containing Scout as a data delivery option."""
    return cases.filter(Case.data_delivery.contains(DataDelivery.SCOUT))


def filter_newer_cases_by_order_date(cases: Query, order_date: datetime, **kwargs) -> Query:
    """Filter cases newer than date."""
    cases: Query = cases.filter(Case.ordered_at > order_date)
    return cases.order_by(Case.ordered_at.asc())


def filter_inactive_analysis_cases(cases: Query, **kwargs) -> Query:
    """Filter cases which are not set or on hold."""
    return cases.filter(
        or_(
            Case.action.is_(None),
            Case.action == CaseActions.HOLD,
        )
    )


def filter_older_cases_by_creation_date(cases: Query, creation_date: datetime, **kwargs) -> Query:
    """Filter older cases compared to date."""
    cases = cases.filter(Case.created_at < creation_date)
    return cases.order_by(Case.created_at.asc())


def filter_report_supported_data_delivery_cases(cases: Query, **kwargs) -> Query:
    """Filter cases with a valid data delivery for delivery report generation."""
    return cases.filter(Case.data_delivery.in_(REPORT_SUPPORTED_DATA_DELIVERY))


def filter_running_cases(cases: Query, **kwargs) -> Query:
    """Filter cases which are running."""
    return cases.filter(Case.action == CaseActions.RUNNING)


def filter_compressible_cases(cases: Query, **kwargs) -> Query:
    """Filter cases which are running."""
    return cases.filter(Case.is_compressible)


def order_cases_by_created_at(cases: Query, **kwargs) -> Query:
    """Order cases by created at."""
    return cases.order_by(Case.created_at.desc())


def filter_cases_pending_or_failed_sequencing_qc(cases: Query, **kwargs) -> Query:
    """Filter cases with pending or failed sequencing QC."""
    return cases.filter(
        or_(
            Case.aggregated_sequencing_qc == SequencingQCStatus.PENDING,
            Case.aggregated_sequencing_qc == SequencingQCStatus.FAILED,
        )
    )


def apply_case_filter(
    cases: Query,
    filter_functions: list[Callable],
    action: str | None = None,
    case_search: str | None = None,
    creation_date: datetime | None = None,
    customer_entry_id: int | None = None,
    customer_entry_ids: list[int] | None = None,
    entry_id: int | None = None,
    internal_id: str | None = None,
    internal_ids: list[str] | None = None,
    internal_id_search: str | None = None,
    name: str | None = None,
    name_search: str | None = None,
    order_date: datetime | None = None,
    workflow: Workflow | None = None,
    workflow_search: str | None = None,
    workflows: list[Workflow] | None = None,
    priority: str | None = None,
    ticket_id: str | None = None,
    order_id: int | None = None,
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
            internal_ids=internal_ids,
            internal_id_search=internal_id_search,
            name=name,
            name_search=name_search,
            order_date=order_date,
            workflow=workflow,
            workflow_search=workflow_search,
            workflows=workflows,
            priority=priority,
            ticket_id=ticket_id,
            order_id=order_id,
        )
    return cases


class CaseFilter(Enum):
    """Define case filters."""

    BY_ACTION: Callable = filter_cases_by_action
    BY_CASE_SEARCH: Callable = filter_cases_by_case_search
    BY_CUSTOMER_ENTRY_ID: Callable = filter_cases_by_customer_entry_id
    BY_CUSTOMER_ENTRY_IDS: Callable = filter_cases_by_customer_entry_ids
    BY_ENTRY_ID: Callable = filter_cases_by_entry_id
    BY_INTERNAL_ID: Callable = filter_case_by_internal_id
    BY_INTERNAL_IDS: Callable = filter_cases_by_internal_ids
    BY_INTERNAL_ID_SEARCH: Callable = filter_cases_by_internal_id_search
    BY_NAME: Callable = filter_cases_by_name
    BY_NAME_SEARCH: Callable = filter_cases_by_name_search
    BY_WORKFLOWS: Callable = filter_cases_by_workflows
    BY_WORKFLOW_SEARCH: Callable = filter_cases_by_workflow_search
    BY_PRIORITY: Callable = filter_cases_by_priority
    FOR_ANALYSIS: Callable = filter_cases_for_analysis
    HAS_INACTIVE_ANALYSIS: Callable = filter_inactive_analysis_cases
    HAS_SEQUENCE: Callable = filter_cases_has_sequence
    IS_RUNNING: Callable = filter_running_cases
    IS_COMPRESSIBLE: Callable = filter_compressible_cases
    NEW_BY_ORDER_DATE: Callable = filter_newer_cases_by_order_date
    NOT_ANALYSED: Callable = filter_cases_not_analysed
    OLD_BY_CREATION_DATE: Callable = filter_older_cases_by_creation_date
    REPORT_SUPPORTED: Callable = filter_report_supported_data_delivery_cases
    WITH_LOQUSDB_SUPPORTED_WORKFLOW: Callable = filter_cases_with_loqusdb_supported_workflow
    WITH_LOQUSDB_SUPPORTED_SEQUENCING_METHOD: Callable = (
        filter_cases_with_loqusdb_supported_sequencing_method
    )
    WITH_WORKFLOW: Callable = filter_cases_with_workflow
    WITH_SCOUT_DELIVERY: Callable = filter_cases_with_scout_data_delivery
    ORDER_BY_CREATED_AT: Callable = order_cases_by_created_at
    PENDING_OR_FAILED_SEQUENCING_QC: Callable = filter_cases_pending_or_failed_sequencing_qc
