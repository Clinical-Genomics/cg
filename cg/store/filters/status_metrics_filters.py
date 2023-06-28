from enum import Enum
from typing import Callable, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Query

from cg.store.models import SampleLaneSequencingMetrics


def filter_total_read_count_for_sample(metrics: Query, sample_internal_id: str, **kwargs) -> Query:
    total_reads_query: Query = metrics.with_entities(
        func.sum(SampleLaneSequencingMetrics.sample_total_reads_in_lane)
    ).filter(SampleLaneSequencingMetrics.sample_internal_id == sample_internal_id)
    return total_reads_query


def filter_metrics_for_flow_cell_sample_internal_id_and_lane(
    metrics: Query, flow_cell_name: str, sample_internal_id: str, lane: int, **kwargs
) -> Query:
    return metrics.filter(
        SampleLaneSequencingMetrics.flow_cell_name == flow_cell_name,
        SampleLaneSequencingMetrics.sample_internal_id == sample_internal_id,
        SampleLaneSequencingMetrics.flow_cell_lane_number == lane,
    )


class SequencingMetricsFilter(Enum):
    FILTER_TOTAL_READ_COUNT_FOR_SAMPLE: Callable = filter_total_read_count_for_sample
    FILTER_METRICS_FOR_FLOW_CELL_SAMPLE_INTERNAL_ID_AND_LANE: Callable = (
        filter_metrics_for_flow_cell_sample_internal_id_and_lane
    )


def apply_metrics_filter(
    metrics: Query,
    filter_functions: List[Callable],
    sample_internal_id: Optional[str] = None,
    flow_cell_name: Optional[str] = None,
    lane: Optional[int] = None,
) -> Query:
    for filter_function in filter_functions:
        metrics: Query = filter_function(
            metrics=metrics,
            sample_internal_id=sample_internal_id,
            flow_cell_name=flow_cell_name,
            lane=lane,
        )
    return metrics
