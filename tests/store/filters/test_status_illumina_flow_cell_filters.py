"""Tests for the illumina flow cell filters in the store."""

from sqlalchemy.orm import Query

from cg.store.filters.status_illumina_flow_cell_filters import (
    filter_illumina_flow_cell_by_internal_id,
)
from cg.store.models import IlluminaFlowCell
from cg.store.store import Store


def test_get_illumina_flow_cell_by_internal_id(
    illumina_flow_cell, illumina_flow_cell_internal_id: str, store: Store
):
    # GIVEN an illumina flow cell
    store.add_illumina_flow_cell(illumina_flow_cell)

    # WHEN adding a new illumina flow cell to the store
    flow_cells: Query = store._get_query(table=IlluminaFlowCell)
    flow_cell: Query = filter_illumina_flow_cell_by_internal_id(
        flow_cells=flow_cells, internal_id=illumina_flow_cell_internal_id
    )

    # THEN it should be stored in the database
    assert isinstance(flow_cell, Query)
    assert flow_cell.first() == illumina_flow_cell
    assert flow_cell.first().internal_id == illumina_flow_cell_internal_id
