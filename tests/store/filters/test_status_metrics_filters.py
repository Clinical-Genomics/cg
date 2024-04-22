from sqlalchemy.orm import Query

from cg.store.filters.status_metrics_filters import (
    filter_above_q30_threshold,
    filter_by_flow_cell_name,
    filter_by_flow_cell_sample_internal_id_and_lane,
    filter_by_sample_internal_id,
    filter_total_read_count_for_sample,
)
from cg.store.models import SampleLaneSequencingMetrics
from cg.store.store import Store


def test_filter_total_read_count_for_sample(
    store_with_sequencing_metrics: Store, sample_id: str, expected_total_reads: int
):
    # GIVEN a Store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # WHEN getting total read counts for a sample
    total_reads_query: Query = filter_total_read_count_for_sample(
        metrics=metrics, sample_internal_id=sample_id
    )

    # THEN assert that the returned object is a Query
    assert isinstance(total_reads_query, Query)

    # THEN a total reads count is returned
    actual_total_reads: int | None = total_reads_query.scalar()
    assert actual_total_reads

    # THEN assert that the actual total read count is as expected
    assert actual_total_reads == expected_total_reads


def test_filter_metrics_for_flow_cell_sample_internal_id_and_lane(
    store_with_sequencing_metrics: Store, sample_id: str, flow_cell_name: str
):
    # GIVEN a Store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # WHEN getting metrics for a flow cell, sample internal id and lane
    metrics_query: Query = filter_by_flow_cell_sample_internal_id_and_lane(
        metrics=metrics,
        flow_cell_name=flow_cell_name,
        sample_internal_id=sample_id,
        lane=1,
    )

    # THEN assert that the returned object is a Query
    assert isinstance(metrics_query, Query)

    # THEN assert that the query returns a list of metrics
    assert metrics_query.all()

    # THEN assert that the query returns the expected number of metrics
    assert len(metrics_query.all()) == 1

    # THEN assert that the query returns the expected metrics
    assert metrics_query[0].flow_cell_name == flow_cell_name
    assert metrics_query[0].sample_internal_id == sample_id
    assert metrics_query[0].flow_cell_lane_number == 1


def test_filter_metrics_by_flow_cell_name(
    store_with_sequencing_metrics: Store, flow_cell_name: str
):
    # GIVEN a Store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # WHEN getting metrics for a flow cell name
    metrics_query: Query = filter_by_flow_cell_name(metrics=metrics, flow_cell_name=flow_cell_name)

    # THEN assert that the returned object is a Query
    assert isinstance(metrics_query, Query)

    # THEN assert that the query returns a list of metrics
    assert metrics_query.all()

    # THEN assert that the query returns the expected number of metrics
    assert len(metrics_query.all()) == 1

    # THEN assert that the query returns the expected metrics
    for metric in metrics_query.all():
        assert metric.flow_cell_name == flow_cell_name


def test_filter_metrics_by_sample_internal_id(store_with_sequencing_metrics: Store, sample_id: str):
    # GIVEN a Store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # WHEN getting metrics for a sample internal id
    metrics_query: Query = filter_by_sample_internal_id(
        sample_internal_id=sample_id, metrics=metrics
    )

    # THEN assert that the returned object is a Query
    assert isinstance(metrics_query, Query)

    # THEN assert that the query returns a list of metrics
    assert metrics_query.all()

    # THEN assert that the query returns the expected number of metrics
    assert len(metrics_query.all()) == 2

    # THEN assert that the query returns the expected metrics
    for metric in metrics_query.all():
        assert metric.sample_internal_id == sample_id


def test_filter_above_q30_threshold(store_with_sequencing_metrics: Store):
    # GIVEN a Store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)
    metric: SampleLaneSequencingMetrics | None = metrics.first()
    assert metric

    # GIVEN a Q30 threshold that at least one metric will pass
    q30_threshold = int(metric.sample_base_percentage_passing_q30 / 2)

    # WHEN filtering metrics above the Q30 threshold
    filtered_metrics: Query = filter_above_q30_threshold(
        metrics=metrics,
        q30_threshold=q30_threshold,
    )

    # THEN assert that the returned object is a Query
    assert isinstance(filtered_metrics, Query)

    # THEN assert that the query returns a list of filtered metrics
    assert filtered_metrics.all()

    # THEN assert that all returned metrics have a sample_base_percentage_passing_q30 greater than the threshold
    for metric in filtered_metrics.all():
        assert metric.sample_base_percentage_passing_q30 > q30_threshold


def test_filter_metrics_by_flow_cell_name(
    store_with_sequencing_metrics: Store, flow_cell_name: str
):
    # GIVEN a Store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # WHEN filtering metrics by flow cell name
    filtered_metrics: Query = filter_by_flow_cell_name(
        metrics=metrics, flow_cell_name=flow_cell_name
    )

    # THEN assert that the returned object is a Query
    assert isinstance(filtered_metrics, Query)

    # THEN assert that the query returns a list of filtered metrics
    assert filtered_metrics.all()

    # THEN assert that all returned metrics have the expected flow cell name
    for metric in filtered_metrics.all():
        assert metric.flow_cell_name == flow_cell_name
