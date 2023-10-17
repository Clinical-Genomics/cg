from cg.store.models import SampleLaneSequencingMetrics


def combine_mapped_metrics_with_undetermined(
    mapped_metrics: list[SampleLaneSequencingMetrics],
    undetermined_metrics: list[SampleLaneSequencingMetrics],
) -> list[SampleLaneSequencingMetrics]:
    """Combine metrics for mapped and undetermined reads."""

    metrics: dict[tuple[str, int], SampleLaneSequencingMetrics] = {
        (metric.sample_internal_id, metric.flow_cell_lane_number): metric
        for metric in mapped_metrics
    }
    for undetermined_metric in undetermined_metrics:
        key = (undetermined_metric.sample_internal_id, undetermined_metric.flow_cell_lane_number)
        existing_metric: SampleLaneSequencingMetrics = metrics.get(key)

        if existing_metric:
            combined_metric: SampleLaneSequencingMetrics = combine_metrics(
                existing_metric=existing_metric, new_metric=undetermined_metric
            )
            metrics[key] = combined_metric
        else:
            metrics[key] = undetermined_metric
    return list(metrics.values())


def combine_metrics(
    existing_metric: SampleLaneSequencingMetrics, new_metric: SampleLaneSequencingMetrics
) -> SampleLaneSequencingMetrics:
    """Update an existing metric with data from a new metric."""

    combined_q30_percentage: float = weighted_average(
        total_1=existing_metric.sample_total_reads_in_lane,
        percentage_1=existing_metric.sample_base_percentage_passing_q30,
        total_2=new_metric.sample_total_reads_in_lane,
        percentage_2=new_metric.sample_base_percentage_passing_q30,
    )
    combined_mean_quality_score: float = weighted_average(
        total_1=existing_metric.sample_total_reads_in_lane,
        percentage_1=existing_metric.sample_base_mean_quality_score,
        total_2=new_metric.sample_total_reads_in_lane,
        percentage_2=new_metric.sample_base_mean_quality_score,
    )
    combined_reads: int = (
        existing_metric.sample_total_reads_in_lane + new_metric.sample_total_reads_in_lane
    )

    existing_metric.sample_base_percentage_passing_q30 = combined_q30_percentage
    existing_metric.sample_base_mean_quality_score = combined_mean_quality_score
    existing_metric.sample_total_reads_in_lane = combined_reads

    return existing_metric


def weighted_average(total_1: int, percentage_1: float, total_2: int, percentage_2: float) -> float:
    """Calculate the weighted average of two percentages."""
    if total_1 == 0 and total_2 == 0:
        return 0
    return (total_1 * percentage_1 + total_2 * percentage_2) / (total_1 + total_2)
