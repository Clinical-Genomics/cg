from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    q30_ratio,
    average_quality_score,
    yield_in_megabases,
    pass_filter_ratio,
    perfect_reads_ratio,
    average_clusters_per_lane,
)


def test_calculate_yield_in_megabases():
    yield_metric: int = yield_in_megabases(total_bases=5000000)
    assert yield_metric == 5


def test_calculate_valid_pass_filter_ratio():
    passed_filter_percent: float = pass_filter_ratio(clusters_passed=100, total_clusters=200)
    assert passed_filter_percent == 0.5


def test_calculate_pass_filter_ratio_when_total_clusters_zero():
    passed_filter_percent: float = pass_filter_ratio(clusters_passed=100, total_clusters=0)
    assert passed_filter_percent == 0


def test_average_clusters_per_lane():
    avg_clusters_per_lane: float = average_clusters_per_lane(total_clusters=100, lane_count=10)
    assert avg_clusters_per_lane == 10


def test_calculate_bases_with_q30_ratio():
    q30_ratio_metric = q30_ratio(q30_yield=100, total_yield=200)
    assert q30_ratio_metric == 0.5


def test_calculate_lane_mean_quality_score():
    avg_quality_score: float = average_quality_score(total_quality_score=100, total_yield=200)
    assert avg_quality_score == 0.5


def test_calculate_perfect_index_reads_ratio():
    perfect_index_reads: float = perfect_reads_ratio(perfect_reads=100, total_reads=200)
    assert perfect_index_reads == 50
