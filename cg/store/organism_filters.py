from enum import Enum
from typing import Callable, List, Optional
from sqlalchemy.orm import Query

from cg.store.models import Organism


def filter_organism_by_internal_id(organisms: Query, internal_id: str, **kwargs) -> Query:
    """Return organism by internal id."""
    return organisms.filter(Organism.internal_id == internal_id)


class OrganismFilter(Enum):
    """Define Organism filter functions."""

    FILTER_BY_INTERNAL_ID: Callable = filter_organism_by_internal_id


def apply_organism_filter(
    organisms: Query,
    filter_functions: List[Callable],
    internal_id: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for filter_function in filter_functions:
        organisms: Query = filter_function(
            organisms=organisms,
            internal_id=internal_id,
        )
    return organisms
