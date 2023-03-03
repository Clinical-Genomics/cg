from enum import Enum
from typing import List, Optional, Callable

from sqlalchemy.orm import Query

from cg.store.models import Collaboration


def get_collaboration_by_internal_id(collaborations: Query, internal_id: str, **kwargs) -> Query:
    """Return collaboration by internal_id."""
    return collaborations.filter(Collaboration.internal_id == internal_id)


class CollaborationFilters(Enum):
    """Define Collaboration filter functions."""

    get_collaboration_by_internal_id: Callable = get_collaboration_by_internal_id


def apply_collaboration_version_filter(
    collaborations: Query,
    functions: List[Callable],
    internal_id: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in functions:
        collaborations: Query = function(
            collaborations=collaborations,
            internal_id=internal_id,
        )
    return collaborations
