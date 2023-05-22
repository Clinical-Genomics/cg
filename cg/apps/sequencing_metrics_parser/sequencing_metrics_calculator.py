def calculate_lane_yield_in_megabases(lane_yield_in_bases: int) -> int:
    """
    Calculate the lane yield in megabases.
    Args:
        lane_yield_in_bases (int): The total yield of the lane in bases.
    Returns:
        int: The yield in megabases.
    """
    return lane_yield_in_bases // 1000000


def calculate_passed_filter_percent(
    total_lane_clusters_passing_filter: int, total_lane_clusters_raw: int
) -> float:
    """
    Calculate the passed filter percent for the lane.
    Args:
        total_lane_clusters_passing_filter (int): The total clusters passing the filter for the lane.
        total_lane_raw_clusters (int): The total number of clusters initially generated for the lane.
    Returns:
        float: The passed filter percent.
    """
    return total_lane_clusters_passing_filter / total_lane_clusters_raw


def calculate_raw_clusters_per_lane_percent(total_raw_clusters: int, number_of_lanes: int) -> float:
    """
    Calculate the raw clusters per lane percent.
    Args:
        total_raw_clusters (int): The total number of clusters initially generated, regardless of quality.
        number_of_lanes (int): The total number of lanes.
    Returns:
        float: The raw clusters per lane percent.
    """
    return total_raw_clusters / number_of_lanes


def calculate_bases_with_q30_percent(yield_q30_total: int, yield_total: int) -> float:
    """
    Calculate the proportion of bases that have a Phred quality score of 30 or more for the lane.
    Args:
        yield_q30_total (int): The sum of all Q30 yields for samples in the lane.
        yield_total (int): The total yield for the lane.
    Returns:
        float: The proportion of bases with Q30 in the lane.
    """
    return yield_q30_total / yield_total


def calculate_lane_mean_quality_score(quality_score_sum_total: int, yield_total: int) -> float:
    """
    Calculate the mean quality score of all the bases for the lane.
    Args:
        quality_score_sum_total (int): The aggregated quality score sum for the lane.
        yield_total (int): The total yield for the lane.
    Returns:
        float: The mean quality score of all the bases for the lane.
    """
    return quality_score_sum_total / yield_total


def calculate_perfect_index_reads_percent(
    perfect_reads_for_sample_in_lane: int, total_reads_for_sample_in_lane: int
) -> float:
    """
    Calculate the perfect index reads percentage.
    Args:
        perfect_reads (int): The number of perfect reads for a sample in a lane.
        total_reads (int): The total number of reads for a sample in a lane.
    Returns:
        float: The perfect index reads percentage.
    """
    return (perfect_reads_for_sample_in_lane / total_reads_for_sample_in_lane) * 100
