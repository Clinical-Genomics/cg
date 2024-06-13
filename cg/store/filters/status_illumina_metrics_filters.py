"""Filters for the Illumina Sample Sequencing Metrics objects."""

from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import (
    IlluminaFlowCell,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Sample,
)


def filter_by_run_id(metrics: Query, run_id: str, **kwargs) -> Query:
    """Filter metrics by run id."""
    joined_query: Query = metrics.join(IlluminaSequencingRun).join(IlluminaFlowCell)
    return joined_query.filter(IlluminaFlowCell.internal_id == run_id)


def filter_by_sample_internal_id(metrics: Query, sample_internal_id: str, **kwargs) -> Query:
    """Filter metrics by sample internal id."""
    joined_query: Query = metrics.join(Sample)
    return joined_query.filter(Sample.internal_id == sample_internal_id)


def filter_by_lane(metrics: Query, lane: int, **kwargs) -> Query:
    """Filter metrics by lane."""
    return metrics.filter(IlluminaSampleSequencingMetrics.flow_cell_lane == lane)


class IlluminaMetricsFilter(Enum):
    BY_RUN_ID: Callable = filter_by_run_id
    BY_SAMPLE_INTERNAL_ID: Callable = filter_by_sample_internal_id
    BY_LANE: Callable = filter_by_lane


def apply_illumina_metrics_filter(
    metrics: Query,
    filter_functions: list[Callable],
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
