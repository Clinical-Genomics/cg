from typing import Optional, List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.store.models import Family, Sample


def get_samples_in_case_by_internal_id(
    case_samples: Query, case_internal_id: str, **kwargs
) -> Query:
    """Return samples associated with a case."""
    return case_samples.filter(Family.internal_id == case_internal_id)


def get_cases_with_sample_by_internal_id(case_samples: Query, sample_internal_id: str, **kwargs):
    """Return cases associated with a sample internal id."""
    return case_samples.filter(Sample.internal_id == sample_internal_id)


def apply_case_sample_filter(
    filter_functions: List[Callable],
    case_samples: Query,
    case_internal_id: Optional[str] = None,
    sample_entry_id: Optional[int] = None,
    sample_internal_id: Optional[str] = None,
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

    GET_SAMPLES_IN_CASE_BY_INTERNAL_ID: Callable = get_samples_in_case_by_internal_id
    GET_CASES_WITH_SAMPLE_BY_INTERNAL_ID: Callable = get_cases_with_sample_by_internal_id
