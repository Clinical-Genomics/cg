from cg.meta.demultiplex.create_non_pooled_metrics import (
    combine_metrics,
    create_sequencing_metrics_for_non_pooled_reads,
    weighted_average,
)
from cg.store.api.core import Store
from cg.store.models import SampleLaneSequencingMetrics


def test_calculates_simple_weighted_average():
    # GIVEN: Equal total counts and different percentages
    total_1, percentage_1 = 50, 0.9
    total_2, percentage_2 = 50, 0.7

    # WHEN: Calculating the weighted average
    result: float = weighted_average(
        total_1=total_1, percentage_1=percentage_1, total_2=total_2, percentage_2=percentage_2
    )

    # THEN: The weighted average should be 0.8
    assert result == 0.8


def test_handles_zero_counts():
    # GIVEN: Zero counts for both totals
    total_1, percentage_1 = 0, 0.0
    total_2, percentage_2 = 0, 0.0

    # WHEN: Calculating the weighted average
    result: float = weighted_average(
        total_1=total_1, percentage_1=percentage_1, total_2=total_2, percentage_2=percentage_2
    )

    # THEN: The weighted average should be zero
    assert result == 0.0


def test_combine_metrics():
    # GIVEN: Two sequencing metrics
    existing_metric = SampleLaneSequencingMetrics(
        sample_total_reads_in_lane=100,
        sample_base_percentage_passing_q30=0.9,
        sample_base_mean_quality_score=30,
    )
    new_metric = SampleLaneSequencingMetrics(
        sample_total_reads_in_lane=100,
        sample_base_percentage_passing_q30=0.8,
        sample_base_mean_quality_score=25,
    )

    # WHEN: Combining the metrics
    combine_metrics(existing_metric=existing_metric, new_metric=new_metric)

    # THEN: The existing metric should be updated
    assert existing_metric.sample_total_reads_in_lane == 200
    assert existing_metric.sample_base_percentage_passing_q30 == 0.85
    assert existing_metric.sample_base_mean_quality_score == 27.5


def test_create_undetermined_metrics_with_no_existing_metrics(store: Store, bcl2fastq_flow_cell):
    # GIVEN: A flow cell demultiplexed with bcl2fastq
    pass
