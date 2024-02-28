from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Collaboration


def filter_collaboration_by_internal_id(collaborations: Query, internal_id: str, **kwargs) -> Query:
    """Return collaboration by internal_id."""
    return collaborations.filter(Collaboration.internal_id == internal_id)


class CollaborationFilter(Enum):
    """Define Collaboration filter functions."""

    BY_INTERNAL_ID: Callable = filter_collaboration_by_internal_id


def apply_collaboration_filter(
    collaborations: Query, filter_functions: list[Callable], internal_id: str | None = None
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        collaborations: Query = function(
            collaborations=collaborations,
            internal_id=internal_id,
        )
    return collaborations
