from cg.services.sample_run_metrics_service.sample_run_metrics_service import (
    SampleRunMetricsService,
)


def test_get_metrics_for_flow_cell(
    sample_run_metrics_service: SampleRunMetricsService,
    novaseq_x_flow_cell_id: str,
):
    # GIVEN an existing flow cell with sequencing metrics

    # WHEN fetching the metrics for the flow cell
    metrics = sample_run_metrics_service.get_metrics(novaseq_x_flow_cell_id)

    # THEN the metrics should be returned
    assert metrics
