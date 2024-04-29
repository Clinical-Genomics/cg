from sqlalchemy.orm import Query

from cg.constants import FlowCellStatus
from cg.store.filters.status_flow_cell_filters import (
    filter_flow_cell_by_name,
    filter_flow_cell_by_name_search,
    filter_flow_cells_by_case,
    filter_flow_cells_with_statuses,
)
from cg.store.models import Case, Flowcell, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_flow_cells_by_case(
    base_store: Store,
    case: Case,
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell case."""

    # GIVEN a flow cell that exist in status db
    helpers.add_flow_cell(
        store=base_store, flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id, samples=[sample]
    )

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: list[Flowcell] | None = filter_flow_cells_by_case(
        flow_cells=base_store._get_join_flow_cell_sample_links_query(), case=case
    )

    # THEN a Flowcell type should be returned
    assert isinstance(returned_flow_cell[0], Flowcell)

    # THEN returned flow cell should have the same name as the flow cell in the database
    assert returned_flow_cell[0].name == novaseq_6000_pre_1_5_kits_flow_cell_id


def test_get_flow_cells_by_case_when_no_flow_cell_for_case(
    base_store: Store,
    case: Case,
):
    """Test that a flow cell is not returned when there is a flow cell with no matching flow cell for case."""

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: list[Flowcell] | None = filter_flow_cells_by_case(
        flow_cells=base_store._get_join_flow_cell_sample_links_query(), case=case
    )

    # THEN returned flow cell should be the original flow cell
    assert not list(returned_flow_cell)


def test_get_flow_cell_by_id(
    base_store: Store, helpers: StoreHelpers, novaseq_6000_pre_1_5_kits_flow_cell_id: str
):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell id."""

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flow_cell(
        store=base_store, flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id
    )

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: Query = filter_flow_cell_by_name(
        flow_cells=base_store._get_query(table=Flowcell),
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
    )

    # THEN returned flow cell should be the original flow cell
    assert isinstance(returned_flow_cell, Query)

    assert flow_cell is returned_flow_cell.first()


def test_get_flow_cell_by_id_and_by_enquiry(
    base_store: Store, helpers: StoreHelpers, novaseq_6000_pre_1_5_kits_flow_cell_id: str
):
    """Test that a flow cell is returned when there is a flow cell with enquiry flow cell id."""

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flow_cell(
        store=base_store, flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id
    )

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell: list[Flowcell] = filter_flow_cell_by_name_search(
        flow_cells=base_store._get_query(table=Flowcell),
        name_search=novaseq_6000_pre_1_5_kits_flow_cell_id[:4],
    )

    # THEN a list of flow cells should be returned
    assert isinstance(returned_flow_cell[0], Flowcell)

    assert flow_cell is returned_flow_cell[0]


def test_get_flow_cells_with_statuses(
    base_store: Store, helpers: StoreHelpers, novaseq_6000_pre_1_5_kits_flow_cell_id: str
):
    """Test that a flow cell is returned when there is a flow cell with matching flow cell id."""

    # GIVEN a flow cell that exist in status db
    helpers.add_flow_cell(store=base_store, flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id)

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell_query: Query = filter_flow_cells_with_statuses(
        flow_cells=base_store._get_query(table=Flowcell),
        flow_cell_statuses=[FlowCellStatus.ON_DISK, FlowCellStatus.PROCESSING],
    )

    # THEN a query should be returned
    assert isinstance(returned_flow_cell_query, Query)


def test_filter_flow_cells_by_name(
    base_store: Store, helpers: StoreHelpers, novaseq_6000_pre_1_5_kits_flow_cell_id: str
):
    """Test flow cell is returned by name."""

    # GIVEN a flow cell that exist in status db
    flow_cell: Flowcell = helpers.add_flow_cell(
        store=base_store, flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id
    )

    # GIVEN a flow cell Query

    # WHEN getting flow cell
    returned_flow_cell_query: Query = filter_flow_cell_by_name(
        flow_cells=base_store._get_query(table=Flowcell), flow_cell_name=flow_cell.name
    )
    returned_flow_cell: Flowcell = returned_flow_cell_query.first()

    # THEN a query should be returned
    assert isinstance(returned_flow_cell_query, Query)

    # THEN the flow cell should have the origin flow cell name
    assert returned_flow_cell.name == flow_cell.name
