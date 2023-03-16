from enum import Enum
from typing import Callable, List, Optional
from sqlalchemy.orm import Query
from cg.store.models import Panel


def filter_panel_by_abbrev(panels: Query, abbreviation: str, **kwargs) -> Query:
    """Return panel by abbreviation."""
    return panels.filter(Panel.abbrev == abbreviation)


class PanelFilter(Enum):
    """Define Panel filter functions."""

    FILTER_BY_ABBREVIATION: Callable = filter_panel_by_abbrev


def apply_panel_filter(
    panels: Query,
    filters: List[PanelFilter],
    abbreviation: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for filter_function in filters:
        panels: Query = filter_function(
            panels=panels,
            abbreviation=abbreviation,
        )
    return panels
