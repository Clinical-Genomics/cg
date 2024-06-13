"""Filters for the Illumina Sequencing Run objects."""

from enum import Enum

from sqlalchemy.orm import Query

from cg.store.models import IlluminaFlowCell


def filter_by_device_internal_id(runs: Query, run_id: str, **kwargs) -> Query:
    """Filter sequencing runs by device internal id."""
    joined_query: Query = runs.join(IlluminaFlowCell)
    return joined_query.filter(IlluminaFlowCell.internal_id == run_id)


class IlluminaSequencingRunFilter(Enum):
    BY_DEVICE_INTERNAL_ID: callable = filter_by_device_internal_id


def apply_illumina_sequencing_run_filter(
    runs: Query,
    filter_functions: list[callable],
    run_id: str | None = None,
) -> Query:
    for filter_function in filter_functions:
        runs: Query = filter_function(
            runs=runs,
            run_id=run_id,
        )
    return runs
