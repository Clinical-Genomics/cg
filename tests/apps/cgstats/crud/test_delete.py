from cg.apps.cgstats.stats import StatsAPI

from cg.apps.cgstats.crud.delete import delete_flowcell
from cg.apps.cgstats.crud.find import get_flowcell_id


def test_delete_flowcell(populated_stats_api: StatsAPI, flowcell_name: str):
    """Test to delete a flowcell from cg-stats"""

    # GIVEN a populated StatsAPI, with an existing flow cell
    flow_cell_id = get_flowcell_id(flowcell_name=flowcell_name)
    assert flow_cell_id

    # WHEN deleting a flow cell from the StatsAPI
    delete_flowcell(manager=populated_stats_api, flowcell_name=flowcell_name)

    # THEN the flowcell should not exist any longer
    results = populated_stats_api.Flowcell.query.filter_by(flowcell_id=flow_cell_id).all()

    assert not results
