from cg.store.models import Flowcell
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_update_flow_cell_has_backup(base_store: Store, flow_cell_name: str, helpers: StoreHelpers):
    """Test updating the backup status of a flow cell in the database."""

    # GIVEN a database containing a flow cell without a back-up
    flow_cell: Flowcell = helpers.add_flow_cell(
        store=base_store, flow_cell_name=flow_cell_name, has_backup=False
    )

    assert not flow_cell.has_backup

    # WHEN updating flow cell attribute has back-up
    base_store.update_flow_cell_has_backup(flow_cell=flow_cell, has_backup=True)

    # THEN flow cell has backup should be true
    assert flow_cell.has_backup
