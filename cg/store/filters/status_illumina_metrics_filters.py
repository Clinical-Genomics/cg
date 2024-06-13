"""Filters for the Illumina Sample Sequencing Metrics objects."""

from enum import Enum

from sqlalchemy.orm import Query

from cg.store.models import IlluminaSampleSequencingMetrics


def filter_by_lane(metrics: Query, lane: int, **kwargs) -> Query:
    """Filter metrics by lane."""
    return metrics.filter(IlluminaSampleSequencingMetrics.flow_cell_lane == lane)


class IlluminaMetricsFilter(Enum):
    BY_LANE: callable = filter_by_lane


def apply_illumina_metrics_filter(
    metrics: Query,
    filter_functions: list[callable],
    sample_internal_id: str | None = None,
    run_id: str | None = None,
    lane: int | None = None,
) -> Query:
    for filter_function in filter_functions:
        metrics: Query = filter_function(
            metrics=metrics,
            run_id=run_id,
            sample_internal_id=sample_internal_id,
            lane=lane,
        )
    return metrics
