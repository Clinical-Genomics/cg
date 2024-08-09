from cg.services.flow_cell_service.flow_cell_service import FlowCellService


def test_get_metrics_for_flow_cell(flow_cell_service: FlowCellService, novaseq_x_flow_cell_id: str):
    # GIVEN an existing flow cell with sequencing metrics

    # WHEN fetching the metrics for the flow cell
    metrics = flow_cell_service.get_sequencing_metrics(novaseq_x_flow_cell_id)

    # THEN the metrics should be returned
    assert metrics
