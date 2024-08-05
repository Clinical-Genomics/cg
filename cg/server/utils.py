from cg.server.dto.sequencing_metrics.sequencing_metrics_request import SequencingMetricsRequest
from cg.store.models import IlluminaSampleSequencingMetrics


def parse_metrics_into_request(
    metrics: list[IlluminaSampleSequencingMetrics],
) -> list[SequencingMetricsRequest]:
    """Parse sequencing metrics into a request."""
    parsed_metrics: list[SequencingMetricsRequest] = []
    for metric in metrics:
        parsed_metric = SequencingMetricsRequest(
            flow_cell_name=metric.instrument_run.device.internal_id,
            flow_cell_lane_number=metric.flow_cell_lane,
            sample_internal_id=metric.sample.internal_id,
            sample_total_reads_in_lane=metric.total_reads_in_lane,
            sample_base_percentage_passing_q30=metric.base_passing_q30_percent,
        )
        parsed_metrics.append(parsed_metric)
    return parsed_metrics
