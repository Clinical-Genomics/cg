from datetime import datetime
from typing import List

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    Bcl2FastqSequencingMetrics,
    ConversionResult,
    DemuxResult,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import parse_bcl2fastq_sequencing_metrics
from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    q30_ratio,
    average_quality_score,
    yield_in_megabases,
    pass_filter_ratio,
    perfect_reads_ratio,
    average_clusters_per_lane,
)
from cg.store.models import SequencingStatistics


def get_sequencing_metrics_from_bcl2fastq(stats_json_path: str):
    """
    Parses the Bcl2fastq generated stats.json file and creates a list of SequencingStatistics objects,
    each representing a sample in a lane on the flow cell.

    Args:
        stats_json_path (str): The path to the JSON file generated by Bcl2fastq.

    Returns:
        List[SequencingStatistics]: A list of SequencingStatistics objects representing the sequencing
        metrics for each sample in each lane on the flow cell.
    """

    raw_sequencing_metrics: Bcl2FastqSequencingMetrics = parse_bcl2fastq_sequencing_metrics(
        stats_json_path=stats_json_path
    )

    sequencing_statistics: List[SequencingStatistics] = []

    for conversion_result in raw_sequencing_metrics.conversion_results:
        for demux_result in conversion_result.demux_results:
            statistics: SequencingStatistics = create_sequencing_statistics(
                conversion_result=conversion_result,
                demux_result=demux_result,
                raw_sequencing_metrics=raw_sequencing_metrics,
            )
            sequencing_statistics.append(statistics)

    return sequencing_statistics


def create_sequencing_statistics(
    conversion_result: ConversionResult,
    demux_result: DemuxResult,
    raw_sequencing_metrics: Bcl2FastqSequencingMetrics,
):
    """
    Generates a SequencingStatistics object based on the provided conversion and demultiplexing results
    along with the raw sequencing metrics.

    Args:
        conversion_result (ConversionResult): A ConversionResult object encapsulating the conversion
        results for a lane.

        demux_result (DemuxResult): A DemuxResult object encapsulating the result of the demultiplexing
        for a sample in a lane.

        raw_sequencing_metrics (Bcl2FastqSequencingMetrics): Raw sequencing metrics parsed from the Bcl2Fastq
        generated stats.json file.

    Returns:
        SequencingStatistics: A SequencingStatistics object that encapsulates the statistics for a sample
        in a lane on the flow cell.
    """
    yield_in_megabases: int = calculate_yield_in_megabases_from_conversion_result(
        conversion_result=conversion_result
    )

    passed_filter_percent: float = calculate_pass_filter_ratio_from_conversion_result(
        conversion_result=conversion_result
    )

    average_quality_score: float = calculate_average_quality_score_from_demux_result(
        demux_result=demux_result
    )

    bases_with_q30_percent: float = calculate_q30_ratio_from_demux_result(demux_result=demux_result)

    perfect_reads_ratio: float = calculate_perfect_reads_ratio_from_demux_result(
        demux_result=demux_result
    )

    number_of_lanes: int = len(raw_sequencing_metrics.conversion_results)
    avg_clusters_per_lane = average_clusters_per_lane(
        total_clusters=conversion_result.total_clusters_raw,
        lane_count=number_of_lanes,
    )

    return SequencingStatistics(
        flow_cell_name=raw_sequencing_metrics.flowcell,
        sample_internal_id=demux_result.sample_id,
        lane=conversion_result.lane_number,
        yield_in_megabases=yield_in_megabases,
        read_counts=demux_result.number_reads,
        passed_filter_percent=passed_filter_percent,
        raw_clusters_per_lane_percent=avg_clusters_per_lane,
        perfect_index_reads_percent=perfect_reads_ratio,
        bases_with_q30_percent=bases_with_q30_percent,
        lanes_mean_quality_score=average_quality_score,
        started_at=datetime.now(),
    )


def calculate_perfect_reads_ratio_from_demux_result(demux_result: DemuxResult):
    """
    Calculate the proportion of perfect index reads for a sample in a lane from the demux result,
    which is the portion of reads with no mismatches in the index.

    Args:
        demux_result (DemuxResult): A DemuxResult object encapsulating the result of the demultiplexing
        for a sample in a lane.

    Returns:
        float: The proportion of perfect index reads for the sample.
    """
    perfect_reads: int = sum(
        [metric.mismatch_counts.get("0", 0) for metric in demux_result.index_metrics]
    )
    total_reads: int = demux_result.number_reads

    return perfect_reads_ratio(perfect_reads=perfect_reads, total_reads=total_reads)


def calculate_q30_ratio_from_demux_result(demux_result: DemuxResult) -> float:
    """
    Calculate the proportion of bases that have a Phred quality score of 30 or more (Q30) for a sample
    in a lane from the demux result.

    Args:
        demux_result (DemuxResult): A DemuxResult object encapsulating the result of the demultiplexing
        for a sample in a lane.

    Returns:
        float: The proportion of Q30 bases for the sample.
    """
    q30_yield = sum([read.yield_q30 for read in demux_result.read_metrics])
    total_yield = sum([read.yield_ for read in demux_result.read_metrics])

    return q30_ratio(q30_yield=q30_yield, total_yield=total_yield)


def calculate_average_quality_score_from_demux_result(demux_result: DemuxResult) -> float:
    """
    Calculate the mean quality score across all bases for a sample in a lane from the demux result.

    Args:
        demux_result (DemuxResult): A DemuxResult object encapsulating the result of the demultiplexing
        for a sample in a lane.

    Returns:
        float: The mean quality score for the sample.
    """
    total_quality_score = sum([read.quality_score_sum for read in demux_result.read_metrics])
    total_yield = sum([read.yield_ for read in demux_result.read_metrics])

    return average_quality_score(total_quality_score=total_quality_score, total_yield=total_yield)


def calculate_yield_in_megabases_from_conversion_result(
    conversion_result: ConversionResult,
) -> int:
    """
    Calculate the total yield in megabases for a lane from the conversion result. The yield is the total
    number of bases generated in the lane.

    Args:
        conversion_result (ConversionResult): A ConversionResult object encapsulating the conversion
        results for a lane.

    Returns:
        int: The yield in megabases for the lane.
    """
    lane_yields_in_bases: List[int] = [demux.yield_ for demux in conversion_result.demux_results]
    total_lane_yield_in_bases: int = sum(lane_yields_in_bases)

    return yield_in_megabases(total_bases=total_lane_yield_in_bases)


def calculate_pass_filter_ratio_from_conversion_result(
    conversion_result: ConversionResult,
) -> float:
    """
    Calculate the proportion of clusters that passed the filter in a lane from the conversion result.
    Clusters passing the filter are those determined to be good quality.

    Args:
        conversion_result (ConversionResult): A ConversionResult object encapsulating the conversion
        results for a lane.

    Returns:
        float: The proportion of clusters that passed the filter for the lane.
    """
    total_clusters: int = conversion_result.total_clusters_raw
    clusters_passed: int = conversion_result.total_clusters_pf

    passed_filter_percent: float = pass_filter_ratio(
        clusters_passed=clusters_passed, total_clusters=total_clusters
    )

    return passed_filter_percent
