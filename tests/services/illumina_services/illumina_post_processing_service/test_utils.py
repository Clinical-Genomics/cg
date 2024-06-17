from datetime import datetime

import math

from cg.constants.devices import DeviceType
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaSampleSequencingMetricsDTO,
)
from cg.services.illumina_services.illumina_post_processing_service.utils import (
    weighted_average,
    combine_metrics,
    combine_sample_metrics_with_undetermined,
)


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


def test_combine_metrics(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN two metrics

    # WHEN Combining the metrics
    existing_metric: IlluminaSampleSequencingMetricsDTO = combine_metrics(
        existing_metric=mapped_metric, new_metric=undetermined_metric
    )

    # THEN The existing metric should be updated
    assert existing_metric.total_reads_in_lane == 200
    assert existing_metric.yield_ == 200


def test_combine_empty_metrics():
    # GIVEN empty lists for mapped and undetermined metrics
    mapped_metrics = []
    undetermined_metrics = []

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be an empty list
    assert combined_metrics == []


def test_combine_metrics_with_only_mapped_metrics(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN one mapped metric and no undetermined
    mapped_metrics = [mapped_metric]
    undetermined_metrics = []

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be the mapped metrics
    assert combined_metrics == mapped_metrics


def test_combine_metrics_with_only_undetermined_metrics(
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN an empty list of mapped metrics and list of undetermined metrics
    mapped_metrics = []
    undetermined_metrics = [undetermined_metric]

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN the result should be the undetermined metrics
    assert combined_metrics == undetermined_metrics


def test_combine_metrics_with_both_mapped_and_undetermined_metrics_different_lanes(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN one mapped and one undetermined metric in different lanes for a sample
    mapped_metrics = [mapped_metric]
    undetermined_metric.flow_cell_lane = 2
    undetermined_metrics = [undetermined_metric]

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=mapped_metrics, undetermined_metrics=undetermined_metrics
    )

    # THEN two metrics should be returned
    assert len(combined_metrics) == 2
    assert combined_metrics[0].flow_cell_lane != combined_metrics[1].flow_cell_lane


def test_combine_metrics_with_both_mapped_and_undetermined_metrics_same_lane(
    mapped_metric: IlluminaSampleSequencingMetricsDTO,
    undetermined_metric: IlluminaSampleSequencingMetricsDTO,
):
    # GIVEN a list of mapped metrics and list of undetermined metrics in the same lane for the same sample

    # WHEN combining them
    combined_metrics = combine_sample_metrics_with_undetermined(
        sample_metrics=[mapped_metric], undetermined_metrics=[undetermined_metric]
    )

    # THEN the combined metrics should be a single metric
    assert len(combined_metrics) == 1

    # THEN the metrics should be a weighted average of the mapped and undetermined metrics
    metric: IlluminaSampleSequencingMetricsDTO = combined_metrics[0]
    assert metric.total_reads_in_lane == 200
    assert metric.yield_ == 200
    assert math.isclose(metric.yield_q30, 0.85, rel_tol=1e-9)
    assert math.isclose(metric.base_passing_q30_percent, 0.85, rel_tol=1e-9)
    assert metric.base_mean_quality_score == 25
