"""Tests for the sequencing metrics dtos."""

from cg.server.utils import parse_metrics_into_request
from cg.store.models import IlluminaSampleSequencingMetrics
from cg.store.store import Store


def test_sequencing_metrics_request(
    store_with_illumina_sequencing_data: Store, novaseq_x_flow_cell_id: str
):
    # GIVEN some sequencing metrics
    sequencing_metrics: list[IlluminaSampleSequencingMetrics] = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_run_by_device_internal_id(
            novaseq_x_flow_cell_id
        ).sample_metrics
    )
    assert sequencing_metrics

    # WHEN parsing the sequencing metrics into a request
    parsed_metrics = parse_metrics_into_request(sequencing_metrics)

    # THEN the parsed metrics should be equal to the original metrics
    for pos in range(1, len(sequencing_metrics)):
        assert (
            sequencing_metrics[pos].instrument_run.device.internal_id
            == parsed_metrics[pos].flow_cell_name
        )
        assert sequencing_metrics[pos].flow_cell_lane == parsed_metrics[pos].flow_cell_lane_number
        assert sequencing_metrics[pos].sample.internal_id == parsed_metrics[pos].sample_internal_id
        assert (
            sequencing_metrics[pos].total_reads_in_lane
            == parsed_metrics[pos].sample_total_reads_in_lane
        )
