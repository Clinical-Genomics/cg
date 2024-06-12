"""Tests for the Illumina Sample Sequencing Metrics filters."""

from sqlalchemy.orm import Query

from cg.store.filters.status_illumina_metrics_filters import (
    filter_by_run_id_sample_internal_id_and_lane,
)
from cg.store.models import IlluminaSampleSequencingMetrics
from cg.store.store import Store


def test_filter_by_run_id_sample_internal_id_and_lane(
    store_with_illumina_sequencing_data: Store,
    novaseq_x_flow_cell_id: str,
    selected_novaseq_x_sample_ids: list[str],
):
    """Test to filter metrics by run id, sample internal id and lane."""
    # GIVEN a store with Illumina Sample Sequencing Metrics for each sample in the run directories
    metrics: Query = store_with_illumina_sequencing_data._get_query(
        table=IlluminaSampleSequencingMetrics
    )
    assert metrics.count() == 14

    # WHEN filtering metrics by run id, sample internal id and lane
    sample_id: str = selected_novaseq_x_sample_ids[0]
    filtered_metrics: Query = filter_by_run_id_sample_internal_id_and_lane(
        metrics=metrics, run_id=novaseq_x_flow_cell_id, sample_internal_id=sample_id, lane=1
    )

    # THEN assert that the returned object is a Query with the desired metrics object
    assert filtered_metrics.count() == 1
    metric: IlluminaSampleSequencingMetrics = filtered_metrics.first()
    assert metric.sample.internal_id == sample_id
    assert metric.flow_cell_lane == 1
    assert metric.instrument_run.device.internal_id == novaseq_x_flow_cell_id
