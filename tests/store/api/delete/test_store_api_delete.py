from cg.store import Store
from cg.store import models


def test_store_api_delete_flowcell(flowcell_name: str, populated_flow_cell_store: Store):
    """Test function to delete a flow cell entry in Store"""

    # GIVEN a database containing a flow cell
    flow_cell: models.Flowcell = populated_flow_cell_store.Flowcell.query.filter(
        models.Flowcell.name == flowcell_name
    ).first()

    assert flow_cell

    # WHEN removing said flow cell
    populated_flow_cell_store.delete_flowcell(flowcell_name=flowcell_name)

    # THEN no entry should be found for said flow cell
    results: models.Flowcell = populated_flow_cell_store.Flowcell.query.filter(
        models.Flowcell.name == flowcell_name
    ).first()

    assert not results
