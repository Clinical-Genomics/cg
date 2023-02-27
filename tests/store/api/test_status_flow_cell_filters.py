from typing import List, Optional

from sqlalchemy.orm import Query

from cg.constants import FlowCellStatus
from cg.store import Store
from cg.store.models import Flowcell, Family, Sample
from cg.store.status_flow_cell_filters import (
    get_flow_cell_by_id,
    get_flow_cells_with_statuses,
    get_flow_cells_by_case,
    get_flow_cell_by_id_and_by_enquiry,
)
from tests.store_helpers import StoreHelpers


def test_get_flow_cells_by_case(
    base_store: Store,
    case_id: str,
    case_obj: Family,
    flow_cell_id: str,
    helpers: StoreHelpers,
    sample_obj: Sample,
):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell case."""

    # GIVEN a flow cell that exist in status db
    helpers.add_flowcell(store=base_store, flow_cell_id=flow_cell_id, samples=[sample_obj])

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: Optional[List[Flowcell]] = get_flow_cells_by_case(
        flow_cells=base_store._get_flow_cell_sample_links_query(), case=case_obj
    )

    # THEN a Flowcell type should be returned
    assert isinstance(returned_flow_cell[0], Flowcell)

    # THEN returned flow cell should have the same name as the flow cell in the database
    assert returned_flow_cell[0].name == flow_cell_id


def test_get_flow_cells_by_case_when_no_flow_cell_for_case(
    base_store: Store,
    case_id: str,
    case_obj: Family,
    flow_cell_id: str,
    helpers: StoreHelpers,
    sample_obj: Sample,
):
    """Test that a flow cell is not returned when there is a flow cell with no matching flow cell for case."""

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: Optional[List[Flowcell]] = get_flow_cells_by_case(
        flow_cells=base_store._get_flow_cell_sample_links_query(), case=case_obj
    )

    # THEN returned flow cell should be the original flow cell
    assert not list(returned_flow_cell)


def test_get_flow_cell_by_id(base_store: Store, helpers: StoreHelpers, flow_cell_id: str):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell id."""

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flowcell(store=base_store, flow_cell_id=flow_cell_id)

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: Flowcell = get_flow_cell_by_id(
        flow_cells=base_store._get_flow_cell_query(), flow_cell_id=flow_cell_id
    )

    # THEN returned flow cell should be the original flow cell
    assert isinstance(returned_flow_cell, Flowcell)

    assert flow_cell is returned_flow_cell


def test_get_flow_cell_by_id_and_by_enquiry(
    base_store: Store, helpers: StoreHelpers, flow_cell_id: str
):
    """Test that a flow cell is returned when there is a flow cell with enquiry flow cell id."""

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flowcell(store=base_store, flow_cell_id=flow_cell_id)

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: List[Flowcell] = get_flow_cell_by_id_and_by_enquiry(
        flow_cells=base_store._get_flow_cell_query(), flow_cell_id=flow_cell_id[:4]
    )

    # THEN a list of flow cells should be returned
    assert isinstance(returned_flow_cell[0], Flowcell)

    assert flow_cell is returned_flow_cell[0]


def test_get_flow_cells_with_statuses(base_store: Store, helpers: StoreHelpers, flow_cell_id: str):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell id."""

    # GIVEN a flow cell that exist in status db
    helpers.add_flowcell(store=base_store, flow_cell_id=flow_cell_id)

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell_query: Query = get_flow_cells_with_statuses(
        flow_cells=base_store._get_flow_cell_query(),
        flow_cell_statuses=[FlowCellStatus.ON_DISK, FlowCellStatus.PROCESSING],
    )

    # THEN a query should be returned
    assert isinstance(returned_flow_cell_query, Query)
