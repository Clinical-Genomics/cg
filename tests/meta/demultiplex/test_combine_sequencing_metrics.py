import math

from cg.meta.demultiplex.combine_sequencing_metrics import (
    combine_mapped_metrics_with_undetermined,
    combine_metrics,
    weighted_average,
)
from cg.store.models import SampleLaneSequencingMetrics


def test_calculates_simple_weighted_average():
    # GIVEN Equal total counts and different percentages
    total_1, percentage_1 = 50, 0.9
    total_2, percentage_2 = 50, 0.7

    # WHEN Calculating the weighted average
    result: float = weighted_average(
        total_1=total_1, percentage_1=percentage_1, total_2=total_2, percentage_2=percentage_2
    )

    # THEN The weighted average should be 0.8
    assert math.isclose(result, 0.8, rel_tol=1e-9)


def test_handles_zero_counts():
    # GIVEN zero counts for totals
    total_1, percentage_1 = 0, 0.0
    total_2, percentage_2 = 0, 0.0

    # WHEN Calculating the weighted average
    result: float = weighted_average(
        total_1=total_1, percentage_1=percentage_1, total_2=total_2, percentage_2=percentage_2
    )

    # THEN The weighted average should be zero
    assert result == 0


def test_combine_metrics():
    # GIVEN two metrics
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

    # WHEN Combining the metrics
    combine_metrics(existing_metric=existing_metric, new_metric=new_metric)

    # THEN The existing metric should be updated
    assert existing_metric.sample_total_reads_in_lane == 200
    assert math.isclose(existing_metric.sample_base_percentage_passing_q30, 0.85, rel_tol=1e-9)
    assert math.isclose(existing_metric.sample_base_mean_quality_score, 27.5, rel_tol=1e-9)


def test_combine_empty_metrics():
    # GIVEN empty lists for mapped and undetermined metrics
    mapped_metrics = []
    undetermined_metrics = []

    # WHEN combining them
    combined_metrics = combine_mapped_metrics_with_undetermined(
        mapped_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be an empty list
    assert combined_metrics == []


def test_combine_metrics_with_only_mapped_metrics():
    # GIVEN one mapped metric and no undetermined
    mapped_metrics = [SampleLaneSequencingMetrics()]
    undetermined_metrics = []

    # WHEN combining them
    combined_metrics = combine_mapped_metrics_with_undetermined(
        mapped_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be the mapped metrics
    assert combined_metrics == mapped_metrics


def test_combine_metrics_with_only_undetermined_metrics():
    # GIVEN an empty list of mapped metrics and list of undetermined metrics
    mapped_metrics = []
    undetermined_metrics = [SampleLaneSequencingMetrics()]

    # WHEN combining them
    combined_metrics = combine_mapped_metrics_with_undetermined(
        mapped_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be the undetermined metrics
    assert combined_metrics == undetermined_metrics


def test_combine_metrics_with_both_mapped_and_undetermined_metrics_different_lanes():
    # GIVEN one mapped and one undetermined metric in different lanes for a sample
    mapped_metrics = [
        SampleLaneSequencingMetrics(flow_cell_lane_number=1, sample_internal_id="sample")
    ]
    undetermined_metrics = [
        SampleLaneSequencingMetrics(flow_cell_lane_number=2, sample_internal_id="sample")
    ]

    # WHEN combining them
    combined_metrics = combine_mapped_metrics_with_undetermined(
        mapped_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN two metrics should be returned
    assert len(combined_metrics) == 2
    assert set(combined_metrics) == set(mapped_metrics + undetermined_metrics)


def test_combine_metrics_with_both_mapped_and_undetermined_metrics_same_lane():
    # GIVEN a list of mapped metrics and list of undetermined metrics in the same lane for the same sample
    mapped_metric = SampleLaneSequencingMetrics(
        sample_internal_id="sample",
        flow_cell_lane_number=1,
        sample_total_reads_in_lane=100,
        sample_base_percentage_passing_q30=0.9,
        sample_base_mean_quality_score=30,
    )

    undetermined_metric = SampleLaneSequencingMetrics(
        sample_internal_id="sample",
        flow_cell_lane_number=1,
        sample_total_reads_in_lane=100,
        sample_base_percentage_passing_q30=0.8,
        sample_base_mean_quality_score=20,
    )

    # WHEN combining them
    combined_metrics = combine_mapped_metrics_with_undetermined(
        mapped_metrics=[mapped_metric], undetermined_metrics=[undetermined_metric]
    )

    # THEN the combined metrics should be a single metric
    assert len(combined_metrics) == 1

    # THEN the metrics should be a weighted average of the mapped and undetermined metrics
    metric: SampleLaneSequencingMetrics = combined_metrics[0]
    assert metric.sample_total_reads_in_lane == 200
    assert math.isclose(metric.sample_base_percentage_passing_q30, 0.85, rel_tol=1e-9)
    assert metric.sample_base_mean_quality_score == 25
