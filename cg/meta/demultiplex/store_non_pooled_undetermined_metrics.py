from typing import List, Optional, Tuple
from cg.apps.sequencing_metrics_parser.api import (
    create_undetermined_sequencing_metrics_for_flow_cell,
)
from cg.meta.demultiplex.status_db_storage_functions import add_sequencing_metrics_to_statusdb
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store.api.core import Store
from cg.store.models import SampleLaneSequencingMetrics


def store_metrics_for_non_pooled_undetermined_reads(
    flow_cell: FlowCellDirectoryData, store: Store
) -> None:
    """Store sequencing metrics for non pooled undetermined reads in status db."""
    non_pooled_lanes_and_samples: List[
        Tuple[int, str]
    ] = flow_cell.sample_sheet.get_non_pooled_lane_sample_id_pairs()

    undetermined_non_pooled_metrics: List[
        SampleLaneSequencingMetrics
    ] = create_undetermined_sequencing_metrics_for_flow_cell(
        flow_cell_directory=flow_cell.path,
        bcl_converter=flow_cell.bcl_converter,
        non_pooled_lanes_and_samples=non_pooled_lanes_and_samples,
    )

    new_metrics: List[SampleLaneSequencingMetrics] = []

    for metrics in undetermined_non_pooled_metrics:
        sample_id: str = metrics.sample_internal_id
        lane: int = metrics.flow_cell_lane_number

        existing_metrics: Optional[
            SampleLaneSequencingMetrics
        ] = store.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
            flow_cell_name=flow_cell.id, sample_internal_id=sample_id, lane=lane
        )
        if existing_metrics:
            combine_metrics(existing_metrics=existing_metrics, new_metrics=metrics)
        else:
            new_metrics.append(metrics)
    add_sequencing_metrics_to_statusdb(sample_lane_sequencing_metrics=new_metrics, store=store)


def combine_metrics(
    existing_metrics: SampleLaneSequencingMetrics, new_metrics: SampleLaneSequencingMetrics
) -> None:
    """Update an existing metric with a new metric."""

    combined_q30_percentage: float = weighted_average(
        total_1=existing_metrics.sample_total_reads_in_lane,
        percentage_1=existing_metrics.sample_base_percentage_passing_q30,
        total_2=new_metrics.sample_total_reads_in_lane,
        percentage_2=new_metrics.sample_base_percentage_passing_q30,
    )
    combined_mean_quality_score: float = weighted_average(
        total_1=existing_metrics.sample_total_reads_in_lane,
        percentage_1=existing_metrics.sample_base_mean_quality_score,
        total_2=new_metrics.sample_total_reads_in_lane,
        percentage_2=new_metrics.sample_base_mean_quality_score,
    )
    combined_reads: int = (
        existing_metrics.sample_total_reads_in_lane + new_metrics.sample_total_reads_in_lane
    )

    existing_metrics.sample_base_percentage_passing_q30 = combined_q30_percentage
    existing_metrics.sample_base_mean_quality_score = combined_mean_quality_score
    existing_metrics.sample_total_reads_in_lane = combined_reads


def weighted_average(total_1: int, percentage_1: float, total_2: int, percentage_2: float) -> float:
    """Calculate the weighted average of two percentages."""
    return (total_1 * percentage_1 + total_2 * percentage_2) / (total_1 + total_2)
