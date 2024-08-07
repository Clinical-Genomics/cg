"""Tests for the Illumina Sample Sequencing Metrics filters."""

from sqlalchemy.orm import Query

from cg.store.filters.status_illumina_metrics_filters import filter_by_lane
from cg.store.models import IlluminaSampleSequencingMetrics
from cg.store.store import Store
from tests.small_helpers import SmallHelpers


def test_filter_by_lane(
    store_with_illumina_sequencing_data: Store,
    seven_canonical_flow_cells_selected_sample_ids: list[list[str]],
    small_helpers: SmallHelpers,
):
    """Test to filter metrics by lane."""
    # GIVEN a store with Illumina Sample Sequencing Metrics for each sample in the run directories
    metrics: Query = store_with_illumina_sequencing_data._get_query(
        table=IlluminaSampleSequencingMetrics
    )
    number_of_samples_in_store: int = small_helpers.length_of_nested_list(
        seven_canonical_flow_cells_selected_sample_ids
    )
    assert metrics.count() == number_of_samples_in_store

    # GIVEN a lane number
    lane: int = 1

    # WHEN filtering metrics by lane
    filtered_metrics: Query = filter_by_lane(metrics=metrics, lane=lane)

    # THEN assert that the function returns a Query of metric objects with the expected lane
    assert filtered_metrics.count() < number_of_samples_in_store
    for metric in filtered_metrics.all():
        assert metric.flow_cell_lane == lane
