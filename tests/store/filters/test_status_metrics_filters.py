from typing import Optional
from cg.store import Store
from cg.store.filters.status_metrics_filters import get_total_read_count_for_sample
from cg.store.models import SampleLaneSequencingMetrics
from sqlalchemy.orm import Query


def test_get_total_read_count_for_sample(
    store_with_sequencing_metrics: Store, sample_id: str, expected_total_reads: int
):
    # GIVEN a Store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # WHEN getting total read counts for a sample
    total_reads_query: Query = get_total_read_count_for_sample(
        metrics=metrics, sample_internal_id=sample_id
    )

    # THEN assert that the returned object is a Query
    assert isinstance(total_reads_query, Query)

    # THEN a total reads count is returned
    actual_total_reads: Optional[int] = total_reads_query.scalar()
    assert actual_total_reads

    # THEN assert that the actual total read count is as expected
    assert actual_total_reads == expected_total_reads
