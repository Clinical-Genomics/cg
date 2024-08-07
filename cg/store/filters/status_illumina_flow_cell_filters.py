"""Filters for the Illumina Flow Cells."""

from enum import Enum

from sqlalchemy.orm import Query


def filter_illumina_flow_cell_by_internal_id(
    flow_cells: Query, internal_id: str, **kwargs
) -> Query:
    """Get an Illumina Flow Cell by its internal id."""
    return flow_cells.filter_by(internal_id=internal_id)


def apply_illumina_flow_cell_filters(
    flow_cells: Query, filter_functions: list[callable], internal_id: str
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        flow_cells: Query = function(
            flow_cells=flow_cells,
            internal_id=internal_id,
        )
    return flow_cells


class IlluminaFlowCellFilter(Enum):
    """Define FlowCell filter functions."""

    BY_INTERNAL_ID: callable = filter_illumina_flow_cell_by_internal_id
