SCALE_TO_MEGABASES = 1_000_000


def yield_in_megabases(total_bases: int) -> float:
    """
    Calculate the yield in megabases.
    Args:
        total_bases (int): The total yield in bases.
    Returns:
        int: The yield in megabases.
    """
    return total_bases / SCALE_TO_MEGABASES


def pass_filter_ratio(clusters_passed: int, total_clusters: int) -> float:
    """
    Calculate the ratio of clusters that passed the filter.
    Args:
        clusters_passed (int): The total clusters in a lane passing the filter.
        total_clusters (int): The total clusters generated in a lane.
    Returns:
        float: The pass filter ratio.
    """
    if total_clusters == 0:
        return 0

    return clusters_passed / total_clusters


def average_clusters_per_lane(total_clusters: int, lane_count: int) -> float:
    """
    Calculate the average number of clusters per lane.
    Args:
        total_clusters (int): Total number of clusters generated.
        lane_count (int): Total number of lanes.
    Returns:
        float: Average clusters per lane.
    """
    return total_clusters / lane_count


def q30_ratio(q30_yield: int, total_yield: int) -> float:
    """
    Calculate the proportion of bases that have a Phred quality score of 30 or more.
    Args:
        q30_yield (int): The sum of all Q30 yields.
        total_yield (int): The total yield.
    Returns:
        float: Proportion of bases with Q30.
    """
    return q30_yield / total_yield


def average_quality_score(total_quality_score: int, total_yield: int) -> float:
    """
    Calculate the average quality score of all bases.
    Args:
        total_quality_score (int): The sum of quality scores.
        total_yield (int): The total yield.
    Returns:
        float: Average quality score of all bases.
    """
    return total_quality_score / total_yield


def perfect_reads_ratio(perfect_reads: int, total_reads: int) -> float:
    """
    Calculate the proportion of perfect reads.
    Args:
        perfect_reads (int): The number of perfect reads for a sample.
        total_reads (int): The total number of reads for a sample.
    Returns:
        float: The perfect reads ratio.
    """
    if total_reads == 0:
        return 0

    return (perfect_reads / total_reads) * 100
