from cg.apps.sequencing_metrics_parser.models import SequencingMetricsForLaneAndSample

from cg.io.json import read_json
from typing import Dict, List


def parse_bcl2fastq_sequencing_metrics(
    stats_json_path: str,
) -> List[SequencingMetricsForLaneAndSample]:
    """Parse data of interest from the Stats.json file generated by the demultiplexing software Bcl2fastq.."""

    raw_sequencing_metrics = read_json(stats_json_path)

    parsed_metrics: List[SequencingMetricsForLaneAndSample] = []

    flow_cell_name = get_flow_cell_name(raw_sequencing_metrics)
    number_of_lanes = get_number_of_lanes_for_flow_cell(raw_sequencing_metrics)

    for conversion_result in raw_sequencing_metrics["ConversionResults"]:
        for demux_result in conversion_result["DemuxResults"]:
            metrics: SequencingMetricsForLaneAndSample = (
                parse_sequencing_metrics_for_sample_in_lane(
                    conversion_result=conversion_result,
                    demux_result=demux_result,
                    number_of_lanes=number_of_lanes,
                    flow_cell_name=flow_cell_name,
                )
            )
            parsed_metrics.append(metrics)

    return parsed_metrics


def parse_sequencing_metrics_for_sample_in_lane(
    conversion_result: Dict, demux_result: Dict, number_of_lanes: int, flow_cell_name: str
) -> SequencingMetricsForLaneAndSample:
    """Parse and validate data for a single lane and sample."""
    lane_number: int = get_lane_number(conversion_result)
    yield_in_bases: int = get_lane_yield_in_bases(conversion_result)
    passing_filter_clusters_count: int = get_total_clusters_passing_filter(conversion_result)

    raw_clusters_count: int = get_total_raw_clusters(conversion_result)
    sample_id: str = get_sample_id(demux_result)
    read_count: int = get_number_of_reads_for_sample_in_lane(demux_result)
    perfect_reads_for_sample: int = get_perfect_reads_for_sample_in_lane(demux_result)
    q30_yield_values: List[int] = get_lane_yield_q30_values(demux_result)
    yield_values: List[int] = get_yield_values(demux_result)
    quality_score_values: List[int] = get_lane_read_quality_score_values(demux_result)

    return SequencingMetricsForLaneAndSample(
        flow_cell_name=flow_cell_name,
        number_of_lanes=number_of_lanes,
        lane_number=lane_number,
        sample_id=sample_id,
        yield_in_bases=yield_in_bases,
        passing_filter_clusters_count=passing_filter_clusters_count,
        raw_clusters_count=raw_clusters_count,
        read_count=read_count,
        perfect_reads_for_sample=perfect_reads_for_sample,
        yield_values=yield_values,
        q30_yield_values=q30_yield_values,
        quality_score_values=quality_score_values,
    )


def get_read_metrics(demux_result: Dict) -> List[Dict]:
    """Extract the read metrics from a demultiplexing result."""
    return demux_result["ReadMetrics"]


def get_index_metrics(demux_result: Dict) -> Dict:
    """Extract the index metrics for a lane from a demultiplexing result."""
    return demux_result["IndexMetrics"][0]


def get_number_of_lanes_for_flow_cell(metrics_data: Dict) -> int:
    """Extract the number of lanes from the stats data."""
    return len(metrics_data["ReadInfosForLanes"])


def get_flow_cell_name(metrics_data: Dict) -> str:
    """Extract the flow cell name from the stats data."""
    return metrics_data["Flowcell"]


def get_sample_id(demux_result: Dict) -> str:
    """Extract the sample id from a demultiplexing result."""
    return demux_result["SampleId"]


def get_number_of_reads_for_sample_in_lane(demux_result: Dict) -> int:
    """Extract the number of reads for a sample in a lane."""
    return demux_result["NumberReads"]


def get_lane_number(conversion_result: Dict) -> int:
    """Extract the lane number from the conversion result."""
    return conversion_result["LaneNumber"]


def get_yield_q30(read_metrics_for_sample_in_lane: Dict) -> int:
    """Extract the yield Q30 from the read metrics."""
    return read_metrics_for_sample_in_lane["YieldQ30"]


def get_lane_yield_in_bases(conversion_result: Dict) -> int:
    """Extract the yield from the read metrics."""
    return conversion_result["Yield"]


def get_total_clusters_passing_filter(conversion_result: Dict) -> int:
    """Extract the total clusters passing the filter from the conversion result."""
    return conversion_result["TotalClustersPF"]


def get_total_raw_clusters(conversion_result: Dict) -> int:
    """Extract the total number of clusters initially generated, regardless of quality."""
    return conversion_result["TotalClustersRaw"]


def get_quality_score(read_metric: Dict) -> int:
    """Extract the sum of quality scores of all the bases from the read metrics."""
    return read_metric["QualityScoreSum"]


def get_lane_yield_q30_values(demux_result: Dict) -> List[int]:
    """Extract the yield Q30 values for the lane from the read metrics."""
    read_metrics_for_sample_in_lane = get_read_metrics(demux_result)
    return [get_yield_q30(metric) for metric in read_metrics_for_sample_in_lane]


def get_yield_values(demux_result: Dict) -> List[int]:
    read_metrics_for_sample_in_lane = get_read_metrics(demux_result)
    return [get_lane_yield_in_bases(metric) for metric in read_metrics_for_sample_in_lane]


def get_lane_read_quality_score_values(demux_result: Dict) -> List[int]:
    """Extract the quality score values for the lane from the read metrics."""
    read_metrics_for_sample_in_lane = get_read_metrics(demux_result)
    return [get_quality_score(read_metric) for read_metric in read_metrics_for_sample_in_lane]


def get_perfect_reads_for_sample_in_lane(demux_result: Dict) -> int:
    """Extract the number of perfect reads for the lane from the read metrics."""
    index_metrics = get_index_metrics(demux_result)
    counts = index_metrics["MismatchCounts"]
    return int(counts.get("0", 0))
