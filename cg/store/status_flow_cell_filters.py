from typing import Optional, List

from sqlalchemy.orm import Query

from cg.store.models import Flowcell


def filter_flow_cell_has_id(flow_cells: Query, flow_cell_id: str, **kwargs) -> Flowcell:
    """Extracts flow cell by flow cell id."""
    return flow_cells.filter(Flowcell.name == flow_cell_id).first()


def filter_flow_cells_with_statuses(
    flow_cells: Query, flow_cell_statuses: List[str], **kwargs
) -> Query:
    """Extracts flow cells by flow cell statuses."""
    # return flow_cells.filter(Flowcell.status == flow_cell_status)
    return flow_cells.filter(Flowcell.status.in_(flow_cell_statuses))


def apply_flow_cell_filter(
    function: str,
    flow_cells: Query,
    flow_cell_id: Optional[str] = None,
    flow_cell_statuses: Optional[List[str]] = None,
) -> Flowcell:
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "flow_cell_has_id": filter_flow_cell_has_id,
        "flow_cells_with_statuses": filter_flow_cells_with_statuses,
    }
    return filter_map[function](
        flow_cells=flow_cells, flow_cell_id=flow_cell_id, flow_cell_statuses=flow_cell_statuses
    )
