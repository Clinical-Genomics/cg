from sqlalchemy.orm import Query

from cg.constants import FlowCellStatus
from cg.store import Store
from cg.store.models import Flowcell
from cg.store.status_flow_cell_filters import filter_flow_cell_has_id, filter_flow_cells_with_status
from tests.store_helpers import StoreHelpers


def test_filter_flow_cell_has_id(base_store: Store, helpers: StoreHelpers, flow_cell_id: str):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell id."""

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flowcell(store=base_store, flow_cell_id=flow_cell_id)

    # GIVEN a flow cell Query
    flow_cells: Query = base_store._get_flow_cell_query()

    # WHEN getting flow cell
    returned_flow_cell: Flowcell = filter_flow_cell_has_id(
        flow_cells=flow_cells, flow_cell_id=flow_cell_id
    )

    # THEN returned flow cell should be the original flow cell
    assert isinstance(returned_flow_cell, Flowcell)

    assert flow_cell is returned_flow_cell


def test_filter_flow_cells_with_status(base_store: Store, helpers: StoreHelpers, flow_cell_id: str):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell id."""

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flowcell(store=base_store, flow_cell_id=flow_cell_id)

    # GIVEN a flow cell Query
    flow_cells: Query = base_store._get_flow_cell_query()

    # WHEN getting flow cell
    returned_flow_cell_query: Query = filter_flow_cells_with_status(
        flow_cells=flow_cells, flow_cell_status=FlowCellStatus.ONDISK
    )

    # THEN a query should be returned
    assert isinstance(returned_flow_cell_query, Query)
