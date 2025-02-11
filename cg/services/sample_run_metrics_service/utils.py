from cg.services.sample_run_metrics_service.dtos import IlluminaSequencingMetricsDTO
from cg.store.models import IlluminaSampleSequencingMetrics


def create_metrics_dto(
    metrics: list[IlluminaSampleSequencingMetrics] | None,
) -> list[IlluminaSequencingMetricsDTO]:

    if not metrics:
        return []

    parsed_metrics = []

    for metric in metrics:
        parsed_metric = IlluminaSequencingMetricsDTO(
            flow_cell_name=metric.instrument_run.device.internal_id,
            flow_cell_lane_number=metric.flow_cell_lane,
            sample_internal_id=metric.sample.internal_id,
            sample_total_reads_in_lane=metric.total_reads_in_lane,
            sample_base_percentage_passing_q30=metric.base_passing_q30_percent,
        )
        parsed_metrics.append(parsed_metric)
    return parsed_metrics
