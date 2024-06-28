"""Tests for the sequencing metrics dtos."""

from cg.server.dto.sequencing_metrics.sequencing_metrics_request import SequencingMetricsRequest
from cg.store.models import SampleLaneSequencingMetrics
from cg.store.store import Store


def test_sequencing_metrics_request(store_with_sequencing_metrics: Store):
    # GIVEN some sequencing metrics
    sequencing_metrics: list[SampleLaneSequencingMetrics] = (
        store_with_sequencing_metrics._get_query(SampleLaneSequencingMetrics).all()
    )
    assert sequencing_metrics

    # WHEN parsing the sequencing metrics into a request
    parsed_metrics = [
        SequencingMetricsRequest.model_validate(metric, from_attributes=True)
        for metric in sequencing_metrics
    ]

    # THEN the parsed metrics should be equal to the original metrics
    for pos in range(1, len(sequencing_metrics)):
        assert sequencing_metrics[pos].flow_cell_name == parsed_metrics[pos].flow_cell_name
        assert (
            sequencing_metrics[pos].flow_cell_lane_number
            == parsed_metrics[pos].flow_cell_lane_number
        )
        assert sequencing_metrics[pos].sample_internal_id == parsed_metrics[pos].sample_internal_id
        assert (
            sequencing_metrics[pos].sample_total_reads_in_lane
            == parsed_metrics[pos].sample_total_reads_in_lane
        )
