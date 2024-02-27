from enum import Enum
from typing import Callable

from sqlalchemy import func
from sqlalchemy.orm import Query

from cg.store.models import SampleLaneSequencingMetrics


def filter_total_read_count_for_sample(metrics: Query, sample_internal_id: str, **kwargs) -> Query:
    """Return total read count for sample across all lanes."""
    total_reads_query: Query = metrics.with_entities(
        func.sum(SampleLaneSequencingMetrics.sample_total_reads_in_lane)
    ).filter(SampleLaneSequencingMetrics.sample_internal_id == sample_internal_id)
    return total_reads_query


def filter_above_q30_threshold(metrics: Query, q30_threshold: int, **kwargs) -> Query:
    """Filter metrics above Q30 threshold and return the ratio."""
    return metrics.filter(
        SampleLaneSequencingMetrics.sample_base_percentage_passing_q30 > q30_threshold,
    )


def filter_by_flow_cell_sample_internal_id_and_lane(
    metrics: Query, flow_cell_name: str, sample_internal_id: str, lane: int, **kwargs
) -> Query:
    """Filter metrics by flow cell name, sample internal id and lane."""
    return metrics.filter(
        SampleLaneSequencingMetrics.flow_cell_name == flow_cell_name,
        SampleLaneSequencingMetrics.sample_internal_id == sample_internal_id,
        SampleLaneSequencingMetrics.flow_cell_lane_number == lane,
    )


def filter_by_flow_cell_name(metrics: Query, flow_cell_name: str, **kwargs) -> Query:
    """Filter metrics by flow cell name."""
    return metrics.filter(
        SampleLaneSequencingMetrics.flow_cell_name == flow_cell_name,
    )


def filter_by_sample_internal_id(metrics: Query, sample_internal_id: str, **kwargs) -> Query:
    """Filter metrics by sample internal id."""
    return metrics.filter(
        SampleLaneSequencingMetrics.sample_internal_id == sample_internal_id,
    )


class SequencingMetricsFilter(Enum):
    TOTAL_READ_COUNT_FOR_SAMPLE: Callable = filter_total_read_count_for_sample
    BY_FLOW_CELL_SAMPLE_INTERNAL_ID_AND_LANE: Callable = (
        filter_by_flow_cell_sample_internal_id_and_lane
    )
    BY_FLOW_CELL_NAME: Callable = filter_by_flow_cell_name
    BY_SAMPLE_INTERNAL_ID: Callable = filter_by_sample_internal_id
    ABOVE_Q30_THRESHOLD: Callable = filter_above_q30_threshold


def apply_metrics_filter(
    metrics: Query,
    filter_functions: list[Callable],
    sample_internal_id: str | None = None,
    flow_cell_name: str | None = None,
    lane: int | None = None,
    q30_threshold: int | None = None,
) -> Query:
    for filter_function in filter_functions:
        metrics: Query = filter_function(
            metrics=metrics,
            sample_internal_id=sample_internal_id,
            flow_cell_name=flow_cell_name,
            lane=lane,
            q30_threshold=q30_threshold,
        )
    return metrics
