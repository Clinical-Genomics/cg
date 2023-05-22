from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    calculate_bases_with_q30_percent,
    calculate_lane_mean_quality_score,
    calculate_lane_yield_in_megabases,
    calculate_passed_filter_percent,
    calculate_perfect_index_reads_percent,
    calculate_raw_clusters_per_lane_percent,
)


def test_calculate_lane_yield_in_megabases():
    assert calculate_lane_yield_in_megabases(5000000) == 5


def test_calculate_passed_filter_percent():
    passed_filter_percent: float = calculate_passed_filter_percent(
        total_lane_clusters_passing_filter=100, total_lane_clusters_raw=200
    )

    assert passed_filter_percent == 0.5


def test_calculate_raw_clusters_per_lane_percent():
    assert calculate_raw_clusters_per_lane_percent(total_raw_clusters=100, number_of_lanes=10) == 10


def test_calculate_bases_with_q30_percent():
    assert calculate_bases_with_q30_percent(yield_q30_total=100, yield_total=200) == 0.5


def test_calculate_lane_mean_quality_score():
    assert calculate_lane_mean_quality_score(quality_score_sum_total=100, yield_total=200) == 0.5


def test_calculate_perfect_index_reads_percent():
    perfect_index_reads_percent: float = calculate_perfect_index_reads_percent(
        perfect_reads_for_sample_in_lane=100, total_reads_for_sample_in_lane=200
    )
    assert perfect_index_reads_percent == 50
