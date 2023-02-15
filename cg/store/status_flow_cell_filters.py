from typing import Optional, List, Union

from sqlalchemy.orm import Query

from cg.store.models import Flowcell, FamilySample, Family


def filter_flow_cells_by_case(flow_cells: Query, case: Family, **kwargs) -> Optional[Query]:
    """Return flow cells by case id."""
    return flow_cells.filter(FamilySample.family == case)


def filter_flow_cell_has_id(flow_cells: Query, flow_cell_id: str, **kwargs) -> Flowcell:
    """Return flow cell by flow cell id."""
    return flow_cells.filter(Flowcell.name == flow_cell_id).first()


def filter_flow_cells_with_statuses(
    flow_cells: Query, flow_cell_statuses: List[str], **kwargs
) -> Optional[Query]:
    """Return flow cells by flow cell statuses."""
    return flow_cells.filter(Flowcell.status.in_(flow_cell_statuses))


def apply_flow_cell_filter(
    function: str,
    flow_cells: Query,
    case: Optional[Family] = None,
    flow_cell_id: Optional[str] = None,
    flow_cell_statuses: Optional[List[str]] = None,
) -> Optional[Union[Query, Flowcell]]:
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "flow_cells_by_case": filter_flow_cells_by_case,
        "flow_cell_has_id": filter_flow_cell_has_id,
        "flow_cells_with_statuses": filter_flow_cells_with_statuses,
    }
    return filter_map[function](
        flow_cells=flow_cells,
        case=case,
        flow_cell_id=flow_cell_id,
        flow_cell_statuses=flow_cell_statuses,
    )
