from cg.store import Store
from cg.store import models


def test_store_api_delete_flowcell(flow_cell_id: str, populated_flow_cell_store: Store):
    """Test function to delete a flow cell entry in Store"""

    # GIVEN a database containing a flow cell
    flow_cell: models.Flowcell = populated_flow_cell_store.Flowcell.query.filter(
        models.Flowcell.name == flow_cell_id
    ).first()

    assert flow_cell

    # WHEN removing said flow cell
    populated_flow_cell_store.delete_flowcell(flowcell_name=flow_cell_id)

    # THEN no entry should be found for said flow cell
    results: models.Flowcell = populated_flow_cell_store.Flowcell.query.filter(
        models.Flowcell.name == flow_cell_id
    ).first()

    assert not results
