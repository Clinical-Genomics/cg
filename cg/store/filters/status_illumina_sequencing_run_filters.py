"""Filters for the Illumina Sequencing Run objects."""

from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import IlluminaSequencingRun


def filter_by_run_internal_id(metrics: Query, run_id: str, **kwargs) -> Query:
    """Filter sequencing runs by run internal id."""
    return metrics.filter(IlluminaSequencingRun.device_id == run_id)


class IlluminaSequencingRunFilter(Enum):
    BY_RUN_INTERNAL_ID: Callable = filter_by_run_internal_id


def apply_illumina_sequencing_run_filter(
    metrics: Query,
    filter_functions: list[Callable],
    run_id: str | None = None,
) -> Query:
    for filter_function in filter_functions:
        metrics: Query = filter_function(
            metrics=metrics,
            run_id=run_id,
        )
    return metrics
