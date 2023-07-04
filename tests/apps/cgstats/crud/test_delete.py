from cg.apps.cgstats.stats import StatsAPI

from cg.apps.cgstats.crud.delete import delete_flowcell


def test_delete_flowcell(populated_stats_api: StatsAPI, flow_cell_name: str):
    """Test to delete a flowcell from cg-stats"""

    # GIVEN a populated StatsAPI, with an existing flow cell
    flow_cell = populated_stats_api.find_handler.get_flow_cell_by_name(
        flow_cell_name=flow_cell_name
    )
    assert flow_cell

    # WHEN deleting a flow cell from the StatsAPI
    delete_flowcell(manager=populated_stats_api, flowcell_name=flow_cell_name)

    # THEN the flowcell should not exist any longer
    results = populated_stats_api.find_handler.get_flow_cell_by_name(flow_cell_name=flow_cell_name)
    assert not results
