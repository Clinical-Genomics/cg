from enum import Enum
from typing import Optional, List, Callable

from sqlalchemy.orm import Query

from cg.store.models import Flowcell, FamilySample, Family


def get_flow_cells_by_case(case: Family, flow_cells: Query, **kwargs) -> Query:
    """Return flow cells by case id."""
    return flow_cells.filter(FamilySample.family == case)


def get_flow_cell_by_id(flow_cells: Query, flow_cell_id: str, **kwargs) -> Query:
    """Return flow cell by flow cell id."""
    return flow_cells.filter(Flowcell.name == flow_cell_id)


def get_flow_cell_by_id_and_by_enquiry(flow_cells: Query, flow_cell_id: str, **kwargs) -> Query:
    """Return flow cell by flow cell id enquiry."""
    return flow_cells.filter(Flowcell.name.like(f"%{flow_cell_id}%"))


def get_flow_cells_with_statuses(
    flow_cells: Query, flow_cell_statuses: List[str], **kwargs
) -> Query:
    """Return flow cells by flow cell statuses."""
    return flow_cells.filter(Flowcell.status.in_(flow_cell_statuses))


def apply_flow_cell_filter(
    flow_cells: Query,
    filter_functions: List[Callable],
    case: Optional[Family] = None,
    flow_cell_id: Optional[str] = None,
    flow_cell_statuses: Optional[List[str]] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        flow_cells: Query = function(
            flow_cells=flow_cells,
            case=case,
            flow_cell_id=flow_cell_id,
            flow_cell_statuses=flow_cell_statuses,
        )
    return flow_cells


class FlowCellFilter(Enum):
    """Define FlowCell filter functions."""

    GET_BY_CASE: Callable = get_flow_cells_by_case
    GET_BY_ID: Callable = get_flow_cell_by_id
    GET_BY_ID_AND_ENQUIRY: Callable = get_flow_cell_by_id_and_by_enquiry
    GET_WITH_STATUSES: Callable = get_flow_cells_with_statuses
