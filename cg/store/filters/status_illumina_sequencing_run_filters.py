"""Filters for the Illumina Sequencing Run objects."""

from enum import Enum

from sqlalchemy.orm import Query

from cg.store.models import IlluminaFlowCell, IlluminaSequencingRun


def filter_by_device_internal_id(runs: Query, device_internal_id: str, **kwargs) -> Query:
    """Filter sequencing runs by device internal id."""
    joined_query: Query = runs.join(IlluminaFlowCell)
    return joined_query.filter(IlluminaFlowCell.internal_id == device_internal_id)


def filter_by_entry_id(runs: Query, entry_id: int, **kwargs) -> Query:
    """Filter sequencing runs by entry id."""
    return runs.filter(IlluminaSequencingRun.id == entry_id)


def filter_by_data_availability(runs: Query, data_availability: list[str], **kwargs) -> Query:
    """Filter sequencing runs by data availability statuses."""
    return runs.filter(IlluminaSequencingRun.data_availability.in_(data_availability))


class IlluminaSequencingRunFilter(Enum):
    BY_DEVICE_INTERNAL_ID: callable = filter_by_device_internal_id
    BY_ENTRY_ID: callable = filter_by_entry_id
    WITH_DATA_AVAILABILITY: callable = filter_by_data_availability


def apply_illumina_sequencing_run_filter(
    runs: Query,
    filter_functions: list[callable],
    device_internal_id: str | None = None,
    entry_id: int | None = None,
    data_availability: list[str] | None = None,
) -> Query:
    for filter_function in filter_functions:
        runs: Query = filter_function(
            runs=runs,
            device_internal_id=device_internal_id,
            entry_id=entry_id,
            data_availability=data_availability,
        )
    return runs
