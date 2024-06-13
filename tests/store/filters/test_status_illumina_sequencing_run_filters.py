"""Tests for the Illumina Sequencing Run filters."""

from sqlalchemy.orm import Query

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.store.filters.status_illumina_sequencing_run_filters import filter_by_device_internal_id
from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store


def test_filter_by_run_internal_id(
    store_with_illumina_sequencing_data: Store,
    novaseq_x_flow_cell_id: str,
    seven_canonical_flow_cells: list[IlluminaRunDirectoryData],
):
    """Test to filter sequencing runs by run internal id."""
    # GIVEN a store with Illumina Sequencing Runs for canonical flow cells
    sequencing_runs: Query = store_with_illumina_sequencing_data._get_query(
        table=IlluminaSequencingRun
    )
    number_of_flow_cells_in_store: int = len(seven_canonical_flow_cells)
    assert sequencing_runs.count() == number_of_flow_cells_in_store

    # WHEN filtering sequencing runs by run internal id
    filtered_runs: Query = filter_by_device_internal_id(
        runs=sequencing_runs, device_internal_id=novaseq_x_flow_cell_id
    )

    # THEN assert that the filtered query has the correct run
    assert filtered_runs.count() < number_of_flow_cells_in_store
    assert filtered_runs.first().device.internal_id == novaseq_x_flow_cell_id
