from typing import Optional, List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.store.models import Family, Sample


def get_samples_associated_with_case(case_samples: Query, case_id: str, **kwargs) -> Query:
    """Return samples associated with a case."""
    return case_samples.filter(Family.internal_id == case_id)


def get_cases_associated_with_sample(case_samples: Query, sample_id: str, **kwargs) -> Query:
    """Return cases associated with a sample."""
    return case_samples.filter(Sample.internal_id == sample_id)


def get_cases_associated_with_sample_by_entry_id(
    case_samples: Query, sample_entry_id: int, **kwargs
) -> Query:
    """Return cases associated with a sample."""
    return case_samples.filter(Sample.id == sample_entry_id)


def apply_case_sample_filter(
    filter_functions: List[Callable],
    case_samples: Query,
    case_id: Optional[str] = None,
    sample_entry_id: Optional[int] = None,
    sample_id: Optional[str] = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for function in filter_functions:
        case_samples: Query = function(
            case_samples=case_samples,
            case_id=case_id,
            sample_entry_id=sample_entry_id,
            sample_id=sample_id,
        )
    return case_samples


class CaseSampleFilter(Enum):
    """Define CaseSample filter functions."""

    GET_SAMPLES_ASSOCIATED_WITH_CASE: Callable = get_samples_associated_with_case
    GET_CASES_ASSOCIATED_WITH_SAMPLE: Callable = get_cases_associated_with_sample
    GET_CASES_ASSOCIATED_WITH_SAMPLE_BY_ENTRY_ID: Callable = (
        get_cases_associated_with_sample_by_entry_id
    )
