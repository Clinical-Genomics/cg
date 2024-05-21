"""Tests for the read illumina flow cell functions in the store."""

from cg.store.models import IlluminaFlowCell
from cg.store.store import Store


def test_get_illumina_flow_cell_by_internal_id(
    illumina_flow_cell: IlluminaFlowCell, illumina_flow_cell_internal_id: str, store: Store
):
    # GIVEN an illumina flow cell
    store.add_illumina_flow_cell(illumina_flow_cell)

    # WHEN adding a new illumina flow cell to the store
    flow_cell: IlluminaFlowCell = store.get_illumina_flow_cell_by_internal_id(
        illumina_flow_cell_internal_id
    )

    # THEN it should be stored in the database
    assert isinstance(flow_cell, IlluminaFlowCell)
    assert flow_cell.internal_id == illumina_flow_cell_internal_id
