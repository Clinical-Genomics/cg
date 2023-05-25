from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    q30_ratio,
    average_quality_score,
    yield_in_megabases,
    pass_filter_ratio,
    perfect_reads_ratio,
    average_clusters_per_lane,
)


def test_calculate_yield_in_megabases():
    """Test calculating the yield in megabases."""
    # GIVEN a number of bases
    total_bases: int = 5_000_000

    # WHEN calculating the yield in megabases
    yield_metric: int = yield_in_megabases(total_bases=total_bases)

    # THEN the yield in megabases should be the number of bases divided by 1 million
    assert yield_metric == 5


def test_calculate_valid_pass_filter_ratio():
    """Test calculating the pass filter ratio."""
    # GIVEN a number of clusters passing the filter and a total number of clusters
    clusters_passed: int = 100
    total_clusters: int = 200

    # WHEN calculating the pass filter ratio
    passed_filter_percent: float = pass_filter_ratio(
        clusters_passed=clusters_passed, total_clusters=total_clusters
    )

    # THEN the pass filter ratio should be the the clusters passing the filter divided by the total clusters
    assert passed_filter_percent == 0.5


def test_calculate_pass_filter_ratio_when_total_clusters_zero():
    """Test calculating the pass filter ratio when the total clusters is zero."""
    # GIVEN a number of clusters passing the filter and a total number of clusters
    clusters_passed: int = 100
    total_clusters: int = 0

    # WHEN calculating the pass filter ratio
    passed_filter_percent: float = pass_filter_ratio(
        clusters_passed=clusters_passed, total_clusters=total_clusters
    )

    # THEN the pass filter ratio should be zero
    assert passed_filter_percent == 0


def test_average_clusters_per_lane():
    """Test calculating the average clusters per lane."""
    # GIVEN a total number of clusters and a number of lanes
    total_clusters: int = 100
    lane_count: int = 10

    # WHEN calculating the average clusters per lane
    avg_clusters_per_lane: float = average_clusters_per_lane(
        total_clusters=total_clusters, lane_count=lane_count
    )

    # THEN the average clusters per lane should be the total clusters divided by the number of lanes
    assert avg_clusters_per_lane == total_clusters / lane_count


def test_calculate_bases_with_q30_ratio():
    """Test calculating q30 ratio."""
    # GIVEN a number of bases with q30 and a total number of bases
    q30_yield: int = 100
    total_yield: int = 200

    # WHEN calculating the q30 ratio
    q30_ratio_metric = q30_ratio(q30_yield=q30_yield, total_yield=total_yield)

    # THEN the q30 ratio should be the number of bases with q30 divided by the total number of bases
    assert q30_ratio_metric == q30_yield / total_yield


def test_calculate_lane_mean_quality_score():
    """Test calculating the average quality score."""
    # GIVEN a total quality score and a total yield
    total_quality_score: int = 100
    total_yield: int = 200

    # WHEN calculating the average quality score
    avg_quality_score: float = average_quality_score(
        total_quality_score=total_quality_score, total_yield=total_yield
    )

    # THEN the average quality score should be the total quality score divided by the total yield
    assert avg_quality_score == total_quality_score / total_yield


def test_calculate_perfect_index_reads_ratio():
    """Test calculating the perfect index reads ratio."""
    # GIVEN a number of perfect reads and a total number of reads
    perfect_reads: int = 100
    total_reads: int = 200

    # WHEN calculating the perfect index reads ratio
    perfect_ratio: float = perfect_reads_ratio(perfect_reads=perfect_reads, total_reads=total_reads)

    # THEN the perfect index reads ratio should be the number of perfect reads divided by the total number of reads
    assert perfect_ratio == perfect_reads / total_reads * 100
