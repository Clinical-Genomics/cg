from typing import Optional

from alchy import Query

from cg.store.models import Flowcell


def filter_flow_cell_has_id(flow_cells: Query, flow_cell_id: str, **kwargs) -> Flowcell:
    """Extracts flow cell by flow cell id."""
    return flow_cells.filter(Flowcell.name == flow_cell_id).first()


def apply_flow_cell_filter(
    function: str, flow_cells: Query, flow_cell_id: Optional[str] = None
) -> Flowcell:
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "flow_cell_has_id": filter_flow_cell_has_id,
    }
    return filter_map[function](flow_cells=flow_cells, flow_cell_id=flow_cell_id)
