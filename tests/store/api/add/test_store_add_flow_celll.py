from datetime import datetime

from cg.constants import FlowCellStatus
from cg.constants.sequencing import Sequencers
from cg.store import Store
from cg.store.models import Flowcell
from tests.store_helpers import StoreHelpers


def test_add_flowcell(
    base_store: Store,
    flow_cell_id: str,
    helpers: StoreHelpers,
    sequencer_name: str,
    timestamp_now: datetime,
):
    """Test adding a flow cell to the database."""

    # GIVEN a database with no flow cell

    # WHEN adding flow cell
    flow_cell: Flowcell = base_store.add_flow_cell(
        flow_cell_id=flow_cell_id,
        sequencer_name=sequencer_name,
        sequencer_type=Sequencers.NOVASEQ,
        date=timestamp_now,
        flow_cell_status=FlowCellStatus.ONDISK,
    )

    # THEN flow cell should be returned
    assert flow_cell

    # THEN the flow cell status should be "ondisk"
    assert flow_cell.status == FlowCellStatus.ONDISK


def test_add_flowcell_status(
    base_store: Store,
    flow_cell_id: str,
    helpers: StoreHelpers,
    sequencer_name: str,
    timestamp_now: datetime,
):
    """Test adding a flow cell with a status to the database."""

    # GIVEN a database with no flow cell

    # WHEN adding flow cell
    flow_cell: Flowcell = base_store.add_flow_cell(
        flow_cell_id=flow_cell_id,
        sequencer_name=sequencer_name,
        sequencer_type=Sequencers.NOVASEQ,
        date=timestamp_now,
        flow_cell_status=FlowCellStatus.PROCESSING,
    )

    # THEN the flow cell status should be "processing"
    assert flow_cell.status == FlowCellStatus.PROCESSING
