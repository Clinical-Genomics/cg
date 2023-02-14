from typing import Optional

from sqlalchemy.orm import Query

from cg.store.models import Flowcell


def filter_flow_cell_has_id(flow_cells: Query, flow_cell_id: str, **kwargs) -> Flowcell:
    """Extracts flow cell by flow cell id."""
    return flow_cells.filter(Flowcell.name == flow_cell_id).first()


def filter_flow_cells_with_status(flow_cells: Query, flow_cell_status: str, **kwargs) -> Query:
    """Extracts flow cells by flow cell status."""
    return flow_cells.filter(Flowcell.status == flow_cell_status)


def apply_flow_cell_filter(
    function: str,
    flow_cells: Query,
    flow_cell_id: Optional[str] = None,
    flow_cell_status: Optional[str] = None,
) -> Flowcell:
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "flow_cell_has_id": filter_flow_cell_has_id,
        "flow_cells_with_status": filter_flow_cells_with_status,
    }
    return filter_map[function](
        flow_cells=flow_cells, flow_cell_id=flow_cell_id, flow_cell_status=flow_cell_status
    )
