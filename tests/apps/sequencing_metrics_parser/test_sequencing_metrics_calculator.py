from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    q30_ratio,
    average_quality_score,
    yield_in_megabases,
    pass_filter_ratio,
    perfect_reads_ratio,
    average_clusters_per_lane,
)


def test_calculate_lane_yield_in_megabases():
    assert yield_in_megabases(total_bases=5000000) == 5


def test_calculate_passed_filter_percent():
    passed_filter_percent: float = pass_filter_ratio(clusters_passed=100, total_clusters=200)

    assert passed_filter_percent == 0.5


def test_calculate_raw_clusters_per_lane_percent():
    assert average_clusters_per_lane(total_clusters=100, lane_count=10) == 10


def test_calculate_bases_with_q30_percent():
    assert q30_ratio(q30_yield=100, total_yield=200) == 0.5


def test_calculate_lane_mean_quality_score():
    assert average_quality_score(total_quality_score=100, total_yield=200) == 0.5


def test_calculate_perfect_index_reads_percent():
    perfect_index_reads_percent: float = perfect_reads_ratio(perfect_reads=100, total_reads=200)
    assert perfect_index_reads_percent == 50
