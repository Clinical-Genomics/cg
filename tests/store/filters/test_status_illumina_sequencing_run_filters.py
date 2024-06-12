"""Tests for the Illumina Sequencing Run filters."""

from sqlalchemy.orm import Query

from cg.store.filters.status_illumina_sequencing_run_filters import filter_by_run_internal_id
from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store


def test_filter_by_run_internal_id(
    store_with_illumina_sequencing_data: Store, novaseq_x_flow_cell_id: str
):
    """Test to filter sequencing runs by run internal id."""
    # GIVEN a store with Illumina Sequencing Runs for canonical flow cells
    sequencing_runs: Query = store_with_illumina_sequencing_data._get_query(
        table=IlluminaSequencingRun
    )
    assert sequencing_runs.count() == 7

    # WHEN filtering sequencing runs by run internal id
    filtered_runs: Query = filter_by_run_internal_id(
        runs=sequencing_runs, run_id=novaseq_x_flow_cell_id
    )

    # THEN assert that the filtered query has the correct run
    assert filtered_runs.count() == 1
    assert filtered_runs.first().device.internal_id == novaseq_x_flow_cell_id
