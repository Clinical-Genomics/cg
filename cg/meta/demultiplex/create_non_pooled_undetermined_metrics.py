from typing import List, Optional
from cg.apps.sequencing_metrics_parser.api import (
    create_undetermined_sequencing_metrics_for_non_pooled_samples_on_flow_cell,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store.api.core import Store
from cg.store.models import SampleLaneSequencingMetrics


def create_sequencing_metrics_for_non_pooled_undetermined_reads(
    flow_cell: FlowCellDirectoryData, store: Store
) -> None:
    """Create and store sequencing metrics for non pooled undetermined reads."""
    undetermined_non_pooled_metrics: List[
        SampleLaneSequencingMetrics
    ] = create_undetermined_sequencing_metrics_for_non_pooled_samples_on_flow_cell(flow_cell)

    new_metrics: List[SampleLaneSequencingMetrics] = []

    for metric in undetermined_non_pooled_metrics:
        sample_id: str = metric.sample_internal_id
        lane: int = metric.flow_cell_lane_number

        existing_metric: Optional[
            SampleLaneSequencingMetrics
        ] = store.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
            flow_cell_name=flow_cell.id, sample_internal_id=sample_id, lane=lane
        )
        if existing_metric:
            combine_metrics(existing_metric=existing_metric, new_metric=metric)
        else:
            new_metrics.append(metric)
    return new_metrics


def combine_metrics(
    existing_metric: SampleLaneSequencingMetrics, new_metric: SampleLaneSequencingMetrics
) -> None:
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


def weighted_average(total_1: int, percentage_1: float, total_2: int, percentage_2: float) -> float:
    """Calculate the weighted average of two percentages."""
    return (total_1 * percentage_1 + total_2 * percentage_2) / (total_1 + total_2)
