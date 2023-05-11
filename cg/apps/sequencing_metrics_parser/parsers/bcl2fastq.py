import json
from typing import List

from cg.store.models import (
    SequencingStatistics,
)


class SequencingMetricsCalculator:
    pass


class SequencingMetricsParser:
    pass


def parse_bcl2fastq_metrics(demultiplexing_directory: str) -> List[SequencingStatistics]:
    """
    Parse the sequencing metrics for a flow cell demultiplexed using bcl2fastq.
    Args:
        demultiplexing_directory: Path to a directory with data from a flow cell demultiplexed with bcl2fastq
    """
    stats = parse_bcl2fastq_stats_json(demultiplexing_directory)
    pass


def parse_bcl2fastq_stats_json(stats_json_path: str) -> List[SequencingStatistics]:
    """Parse data of interest from the Stats.json file generated by bcl2fastq."""

    with open(stats_json_path) as f:
        data = json.load(f)

    number_of_lanes = get_number_of_lanes_from_stats(data)
    flow_cell_name = get_flow_cell_name(data)

    sequencing_statistics = []
    for conversion_result in data["ConversionResults"]:
        for lane_demultiplexing_result in conversion_result["DemuxResults"]:
            statistics = create_sequencing_statistics(
                conversion_result, lane_demultiplexing_result, number_of_lanes, flow_cell_name
            )
            sequencing_statistics.append(statistics)

    return sequencing_statistics


def create_sequencing_statistics(
    conversion_result, lane_demultiplexing_result, number_of_lanes, flow_cell_name
):
    sample_id = get_sample_id(lane_demultiplexing_result)
    lane_number = get_lane_number(conversion_result)
    read_counts = get_number_of_reads(lane_demultiplexing_result)

    yield_in_megabases = calculate_yield_in_megabases(conversion_result)
    passed_filter_percent = calculate_passed_filter_percent(conversion_result)
    raw_clusters_per_lane_percent = calculate_raw_clusters_per_lane_percent(
        conversion_result, number_of_lanes
    )

    lane_read_metrics = get_read_metrics(lane_demultiplexing_result)
    bases_with_q30_percent = calculate_bases_with_q30_percent(lane_read_metrics)
    lanes_mean_quality_score = calculate_lanes_mean_quality_score(lane_read_metrics)
    perfect_index_reads_percent = calculate_perfect_index_reads_percent(lane_read_metrics)

    return SequencingStatistics(
        flow_cell_name=flow_cell_name,
        sample_internal_id=sample_id,
        lane=lane_number,
        read_counts=read_counts,
        yield_in_megabases=yield_in_megabases,
        passed_filter_percent=passed_filter_percent,
        raw_clusters_per_lane_percent=raw_clusters_per_lane_percent,
        bases_with_q30_percent=bases_with_q30_percent,
        lanes_mean_quality_score=lanes_mean_quality_score,
        perfect_index_reads_percent=perfect_index_reads_percent,
    )


def get_read_metrics(lane_demultiplexing_result):
    """Extract the read metrics for a lane from a demultiplexing result."""
    return lane_demultiplexing_result["ReadMetrics"]


def get_number_of_lanes_from_stats(stats_data) -> int:
    """Extract the number of lanes from the stats data."""
    return len(stats_data["ReadInfosForLanes"])


def get_flow_cell_name(stats_data) -> str:
    """Extract the flow cell name from the stats data."""
    return stats_data["Flowcell"]


def get_sample_id(lane_demultiplexing_result):
    """Extract the sample id from a demultiplexing result."""
    return lane_demultiplexing_result["SampleId"]


def get_number_of_reads(lane_demultiplexing_result):
    """Extract the number of reads from a demultiplexing result."""
    return lane_demultiplexing_result["NumberReads"]


def get_lane_number(conversion_result):
    """Extract the lane number from a conversion result."""
    return conversion_result["LaneNumber"]


def get_yield_q30(lane_read_metrics):
    """Extract the yield Q30 from the read metrics."""
    return lane_read_metrics["YieldQ30"]


def get_yield(conversion_result):
    """Extract the yield from the read metrics."""
    return conversion_result["Yield"]


def get_total_clusters_passing_filter(conversion_result):
    """Extract the total clusters passing the filter from the conversion result."""
    return conversion_result["TotalClustersPF"]


def get_total_raw_clusters(conversion_result):
    """Extract the total number of clusters initially generated, regardless of quality."""
    return conversion_result["TotalClustersRaw"]


def get_quality_scores(read_metric):
    """Extract the sum of quality scores of all the bases from the read metrics."""
    return read_metric["QualityScoreSum"]


def calculate_aggregate_yield_q30(lane_read_metrics):
    """Calculate the aggregated Q30 yield for the lane from the read metrics."""
    return sum(get_yield_q30(metric) for metric in lane_read_metrics)


def calculate_aggregate_yield(read_metrics):
    return sum(get_yield(metric) for metric in read_metrics)


def calculate_aggregate_quality_score_sum(lane_read_metrics):
    """Calculate the aggregated quality score sum for the lane from the read metrics."""
    return sum(get_quality_scores(read_metric) for read_metric in lane_read_metrics)


def calculate_yield_in_megabases(conversion_result):
    """Calculate the yield in megabases for the lane from the conversion result."""
    conversion_yield = get_yield(conversion_result)
    return conversion_yield // 1000000


def calculate_passed_filter_percent(conversion_result):
    """Calculate the passed filter percent for the lane from the conversion result."""
    total_clusters_passing_filter = get_total_clusters_passing_filter(conversion_result)
    total_raw_clusters = get_total_raw_clusters(conversion_result)
    return total_clusters_passing_filter / total_raw_clusters


def calculate_raw_clusters_per_lane_percent(conversion_result, number_of_lanes):
    """Calculate the raw clusters per lane percent from the conversion result."""
    total_raw_clusters = get_total_raw_clusters(conversion_result)
    return total_raw_clusters / number_of_lanes


def calculate_bases_with_q30_percent(lane_read_metrics):
    """Calculate the proportion of bases that have a Phred quality score of 30 or more for the lane."""
    yield_q30_total = calculate_aggregate_yield_q30(lane_read_metrics)
    yield_total = calculate_aggregate_yield(lane_read_metrics)
    return yield_q30_total / yield_total


def calculate_lanes_mean_quality_score(lane_read_metrics):
    """Calculate the mean quality score of all the bases for the lane."""
    quality_score_sum_total = calculate_aggregate_quality_score_sum(lane_read_metrics)
    yield_total = calculate_aggregate_yield(lane_read_metrics)
    return quality_score_sum_total / yield_total


def calculate_perfect_index_reads_percent(demux_result):
    """
    Calculate the perfect index reads percentage for a sample.

    The perfect index reads percentage is defined as the number of reads with 0 mismatches
    divided by the total number of reads, multiplied by 100.

    Assumes that there is only one index metric per sample in the demultiplexing result.
    """
    index_metric = demux_result["IndexMetrics"][0]
    mismatch_counts = index_metric["MismatchCounts"]
    perfect_reads = int(mismatch_counts.get("0", 0))
    mismatch_reads = int(mismatch_counts.get("1", 0))
    total_reads = perfect_reads + mismatch_reads

    perfect_index_reads_percent = (perfect_reads / total_reads) * 100

    return perfect_index_reads_percent
