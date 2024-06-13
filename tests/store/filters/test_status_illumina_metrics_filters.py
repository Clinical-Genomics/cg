"""Tests for the Illumina Sample Sequencing Metrics filters."""

from sqlalchemy.orm import Query

from cg.store.filters.status_illumina_metrics_filters import (
    filter_by_lane,
    filter_by_run_id,
    filter_by_sample_internal_id,
)
from cg.store.models import IlluminaSampleSequencingMetrics
from cg.store.store import Store


def test_filter_by_run_id(store_with_illumina_sequencing_data: Store, novaseq_x_flow_cell_id: str):
    """Test to filter metrics by run id."""
    # GIVEN a store with Illumina Sample Sequencing Metrics for each sample in the run directories
    metrics: Query = store_with_illumina_sequencing_data._get_query(
        table=IlluminaSampleSequencingMetrics
    )
    assert metrics.count() == 14

    # WHEN filtering metrics by run id
    filtered_metrics: Query = filter_by_run_id(metrics=metrics, run_id=novaseq_x_flow_cell_id)

    # THEN assert that the function returns a Query of metric objects with the expected run id
    assert filtered_metrics.count() < 14
    for metric in filtered_metrics.all():
        assert metric.instrument_run.device.internal_id == novaseq_x_flow_cell_id


def test_filter_by_sample_internal_id(
    store_with_illumina_sequencing_data: Store, selected_novaseq_x_sample_ids: list[str]
):
    """Test to filter metrics by sample internal id."""
    # GIVEN a store with Illumina Sample Sequencing Metrics for each sample in the run directories
    metrics: Query = store_with_illumina_sequencing_data._get_query(
        table=IlluminaSampleSequencingMetrics
    )
    assert metrics.count() == 14

    # WHEN filtering metrics by sample internal id
    sample_id: str = selected_novaseq_x_sample_ids[0]
    filtered_metrics: Query = filter_by_sample_internal_id(
        metrics=metrics, sample_internal_id=sample_id
    )

    # THEN assert that the function returns a Query of metric objects with the expected sample id
    assert filtered_metrics.count() < 14
    for metric in filtered_metrics.all():
        assert metric.sample.internal_id == sample_id


def test_filter_by_lane(store_with_illumina_sequencing_data: Store):
    """Test to filter metrics by lane."""
    # GIVEN a store with Illumina Sample Sequencing Metrics for each sample in the run directories
    metrics: Query = store_with_illumina_sequencing_data._get_query(
        table=IlluminaSampleSequencingMetrics
    )
    assert metrics.count() == 14

    # GIVEN a lane number
    lane: int = 1

    # WHEN filtering metrics by lane
    filtered_metrics: Query = filter_by_lane(metrics=metrics, lane=lane)

    # THEN assert that the function returns a Query of metric objects with the expected lane
    assert filtered_metrics.count() < 14
    for metric in filtered_metrics.all():
        assert metric.flow_cell_lane == lane
