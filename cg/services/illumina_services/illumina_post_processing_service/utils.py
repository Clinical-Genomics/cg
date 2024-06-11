"""Utility functions for the Illumina post-processing service."""

from pathlib import Path


from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaSampleSequencingMetricsDTO,
)


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()


def combine_sample_metrics_with_undetermined(
    sample_metrics: list[IlluminaSampleSequencingMetricsDTO],
    undetermined_metrics: list[IlluminaSampleSequencingMetricsDTO],
) -> list[IlluminaSampleSequencingMetricsDTO]:
    """Combine metrics for sample metrics with metrics for undetermined reads.
    This occurs only if a sample is the only sample in a lane.
    """

    metrics: dict[tuple[str, int], IlluminaSampleSequencingMetricsDTO] = {
        (metric.sample_id, metric.flow_cell_lane): metric for metric in sample_metrics
    }
    for undetermined_metric in undetermined_metrics:
        key = (
            undetermined_metric.sample_id,
            undetermined_metric.flow_cell_lane,
        )
        existing_metric: IlluminaSampleSequencingMetricsDTO = metrics.get(key)

        if existing_metric:
            combined_metric: IlluminaSampleSequencingMetricsDTO = combine_metrics(
                existing_metric=existing_metric, new_metric=undetermined_metric
            )
            metrics[key] = combined_metric
        else:
            metrics[key] = undetermined_metric
    return list(metrics.values())


def combine_metrics(
    existing_metric: IlluminaSampleSequencingMetricsDTO,
    new_metric: IlluminaSampleSequencingMetricsDTO,
) -> IlluminaSampleSequencingMetricsDTO:
    """Update an existing metric with data from a new metric."""

    combined_q30_percentage: float = weighted_average(
        total_1=existing_metric.total_reads_in_lane,
        percentage_1=existing_metric.base_passing_q30_percent,
        total_2=new_metric.total_reads_in_lane,
        percentage_2=new_metric.base_passing_q30_percent,
    )
    combined_mean_quality_score: float = weighted_average(
        total_1=existing_metric.total_reads_in_lane,
        percentage_1=existing_metric.base_mean_quality_score,
        total_2=new_metric.total_reads_in_lane,
        percentage_2=new_metric.base_mean_quality_score,
    )
    combined_yield_q30_percentage: float = weighted_average(
        total_1=existing_metric.yield_,
        percentage_1=existing_metric.yield_q30,
        total_2=new_metric.yield_,
        percentage_2=new_metric.yield_q30,
    )
    combined_reads: int = existing_metric.total_reads_in_lane + new_metric.total_reads_in_lane
    combined_yield: int = existing_metric.yield_ + new_metric.yield_

    existing_metric.base_passing_q30_percent = combined_q30_percentage
    existing_metric.base_mean_quality_score = combined_mean_quality_score
    existing_metric.total_reads_in_lane = combined_reads
    existing_metric.yield_ = combined_yield
    existing_metric.yield_q30 = combined_yield_q30_percentage

    return existing_metric


def weighted_average(total_1: int, percentage_1: float, total_2: int, percentage_2: float) -> float:
    """Calculate the weighted average of two percentages."""
    if total_1 == 0 and total_2 == 0:
        return 0
    return (total_1 * percentage_1 + total_2 * percentage_2) / (total_1 + total_2)
