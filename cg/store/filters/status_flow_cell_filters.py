from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Case, CaseSample, Flowcell


def filter_flow_cells_by_case(case: Case, flow_cells: Query, **kwargs) -> Query:
    """Return flow cells by case id."""
    return flow_cells.filter(CaseSample.case == case)


def filter_flow_cell_by_name(flow_cells: Query, flow_cell_name: str, **kwargs) -> Query:
    """Return flow cell by flow cell id."""
    return flow_cells.filter(Flowcell.name == flow_cell_name)


def apply_flow_cell_filter(
    flow_cells: Query,
    filter_functions: list[Callable],
    case: Case | None = None,
    flow_cell_name: str | None = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        flow_cells: Query = function(
            flow_cells=flow_cells,
            case=case,
            flow_cell_name=flow_cell_name,
        )
    return flow_cells


class FlowCellFilter(Enum):
    """Define FlowCell filter functions."""

    BY_CASE: Callable = filter_flow_cells_by_case
    BY_NAME: Callable = filter_flow_cell_by_name
