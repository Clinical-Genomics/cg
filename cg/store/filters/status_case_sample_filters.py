from enum import Enum
from typing import Callable

from sqlalchemy import not_
from sqlalchemy.orm import Query

from cg.store.models import Case, Sample


def filter_samples_in_case_by_internal_id(
    case_samples: Query, case_internal_id: str, **kwargs
) -> Query:
    """Return samples associated with a case."""
    return case_samples.filter(Case.internal_id == case_internal_id)


def filter_cases_with_sample_by_internal_id(case_samples: Query, sample_internal_id: str, **kwargs):
    """Return cases associated with a sample internal id."""
    return case_samples.filter(Sample.internal_id == sample_internal_id)


def filter_by_order(case_samples: Query, order_id: int, **kwargs) -> Query:
    return case_samples.filter(Case.order_id == order_id)


def get_not_received_cases(case_samples: Query, **kwargs) -> Query:
    some_samples_not_received_condition = Case.links.any(Sample.received_at == None)
    return case_samples.filter(some_samples_not_received_condition).distinct()


def get_received_cases(case_samples: Query, **kwargs) -> Query:
    all_samples_received_condition = not_(Case.links.any(Sample.received_at == None))
    return case_samples.filter(all_samples_received_condition).distinct()


def get_not_prepared_cases(case_samples: Query, **kwargs) -> Query:
    some_samples_not_prepared_condition = Case.links.any(Sample.prepared_at == None)
    return case_samples.filter(some_samples_not_prepared_condition).distinct()


def get_prepared_cases(case_samples: Query, **kwargs) -> Query:
    all_samples_prepared_condition = not_(Case.links.any(Sample.prepared_at == None))
    return case_samples.filter(all_samples_prepared_condition).distinct()


def get_not_sequenced_cases(case_samples: Query, **kwargs) -> Query:
    some_samples_not_sequenced_condition = Case.links.any(Sample.last_sequenced_at == None)
    return case_samples.filter(some_samples_not_sequenced_condition).distinct()


def apply_case_sample_filter(
    filter_functions: list[Callable],
    case_samples: Query,
    case_internal_id: str | None = None,
    sample_entry_id: int | None = None,
    sample_internal_id: str | None = None,
    order_id: int | None = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for function in filter_functions:
        case_samples: Query = function(
            case_samples=case_samples,
            case_internal_id=case_internal_id,
            sample_entry_id=sample_entry_id,
            sample_internal_id=sample_internal_id,
            order_id=order_id,
        )
    return case_samples


class CaseSampleFilter(Enum):
    """Define CaseSample filter functions."""

    SAMPLES_IN_CASE_BY_INTERNAL_ID: Callable = filter_samples_in_case_by_internal_id
    CASES_WITH_SAMPLE_BY_INTERNAL_ID: Callable = filter_cases_with_sample_by_internal_id
    CASES_WITH_SAMPLES_NOT_RECEIVED: Callable = get_not_received_cases
    CASES_WITH_ALL_SAMPLES_RECEIVED: Callable = get_received_cases
    CASES_WITH_SAMPLES_NOT_PREPARED: Callable = get_not_prepared_cases
    CASES_WITH_ALL_SAMPLES_PREPARED: Callable = get_prepared_cases
    CASES_WITH_SAMPLES_NOT_SEQUENCED: Callable = get_not_sequenced_cases
    BY_ORDER: Callable = filter_by_order
