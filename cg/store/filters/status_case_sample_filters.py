from enum import Enum
from typing import Callable

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


def apply_case_sample_filter(
    filter_functions: list[Callable],
    case_samples: Query,
    case_internal_id: str | None = None,
    sample_entry_id: int | None = None,
    sample_internal_id: str | None = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for function in filter_functions:
        case_samples: Query = function(
            case_samples=case_samples,
            case_internal_id=case_internal_id,
            sample_entry_id=sample_entry_id,
            sample_internal_id=sample_internal_id,
        )
    return case_samples


class CaseSampleFilter(Enum):
    """Define CaseSample filter functions."""

    SAMPLES_IN_CASE_BY_INTERNAL_ID: Callable = filter_samples_in_case_by_internal_id
    CASES_WITH_SAMPLE_BY_INTERNAL_ID: Callable = filter_cases_with_sample_by_internal_id
