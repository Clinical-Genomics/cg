"""Filters for the Illumina Sample Sequencing Metrics objects."""

from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import IlluminaSampleSequencingMetrics


def filter_by_run_id_sample_internal_id_and_lane(
    metrics: Query, run_id: str, sample_internal_id: str, lane: int, **kwargs
) -> Query:
    """Filter metrics by flow cell name, sample internal id and lane."""
    return metrics.filter(
        IlluminaSampleSequencingMetrics.instrument_run_id == run_id,
        IlluminaSampleSequencingMetrics.sample.internal_id == sample_internal_id,
        IlluminaSampleSequencingMetrics.flow_cell_lane == lane,
    )


class IlluminaMetricsFilter(Enum):
    BY_RUN_ID_SAMPLE_INTERNAL_ID_AND_LANE: Callable = filter_by_run_id_sample_internal_id_and_lane


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
