from enum import Enum
from typing import Callable, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Query

from cg.store.models import SampleLaneSequencingMetrics


def get_total_read_count_for_sample(metrics: Query, sample_internal_id: str, **kwargs) -> Query:
    total_reads_query: Query = metrics.with_entities(
        func.sum(SampleLaneSequencingMetrics.sample_total_reads_in_lane)
    ).filter(SampleLaneSequencingMetrics.sample_internal_id == sample_internal_id)
    return total_reads_query


class SequencingMetricsFilter(Enum):
    GET_TOTAL_READ_COUNT_FOR_SAMPLE: Callable = get_total_read_count_for_sample


def apply_metrics_filter(
    metrics: Query,
    filter_functions: List[Callable],
    sample_internal_id: Optional[str] = None,
) -> Query:
    for filter_function in filter_functions:
        metrics: Query = filter_function(
            metrics=metrics,
            sample_internal_id=sample_internal_id,
        )
    return metrics
