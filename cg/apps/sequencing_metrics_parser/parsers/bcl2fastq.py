from cg.io.json import read_json
from pydantic import BaseModel, Field, validator
from typing import List


class SequencingMetricsPerLaneAndSample(BaseModel):
    """
    Contains the parsed bcl2fastq sequencing metrics output.
    The data is parsed per lane and sample and is validated.
    """

    flow_cell_name: str = Field(..., min_length=1)
    number_of_lanes: int = Field(..., gt=0)
    lane_number: int = Field(..., ge=0)
    sample_id: str = Field(..., min_length=1)

    yield_in_bases: int = Field(..., ge=0)
    passing_filter_clusters_count: int = Field(..., ge=0)
    raw_clusters_count: int = Field(..., ge=0)
    read_count: int = Field(..., gt=0)
    perfect_reads_for_sample: int = Field(..., gt=0)
    yield_values: List[int] = Field(min_items=0)
    q30_yield_values: List[int] = Field(min_items=0)
    quality_score_values: List[int] = Field(min_items=0)

    @validator("yield_values", "q30_yield_values", "quality_score_values", each_item=True)
    def check_non_negative(cls, value):
        if value < 0:
            raise ValueError("List values must be non-negative")
        return value


def parse_bcl2fastq_sequencing_metrics(
    stats_json_path: str,
) -> List[SequencingMetricsPerLaneAndSample]:
    """Parse data of interest from the Stats.json file generated by bcl2fastq."""

    data = read_json(stats_json_path)

    parsed_metrics = []

    flow_cell_name = get_flow_cell_name(data)
    number_of_lanes = get_number_of_lanes_for_flow_cell(data)

    for conversion_result in data["ConversionResults"]:
        for demux_result in conversion_result["DemuxResults"]:
            metrics = SequencingMetricsPerLaneAndSample()

            metrics.flow_cell_name = flow_cell_name
            metrics.lane_number = get_lane_number(conversion_result)
            metrics.number_of_lanes = number_of_lanes
            metrics.yield_in_bases = get_lane_yield_in_bases(conversion_result)
            metrics.passing_filter_clusters_count = get_total_clusters_passing_filter(
                conversion_result
            )

            metrics.raw_clusters_count = get_total_raw_clusters(conversion_result)
            metrics.sample_id = get_sample_id(demux_result)
            metrics.read_count = get_number_of_reads_for_sample_in_lane(demux_result)
            metrics.perfect_reads_for_sample = get_perfect_reads_for_sample_in_lane(demux_result)
            metrics.q30_yield_values = get_lane_yield_q30_values(demux_result)
            metrics.yield_values = get_yield_values(demux_result)
            metrics.quality_score_values = get_lane_read_quality_score_values(demux_result)

            parsed_metrics.append(metrics)

    return parsed_metrics


def get_read_metrics(demux_result):
    """Extract the read metrics for a lane from a demultiplexing result."""
    return demux_result["ReadMetrics"]


def get_index_metrics(demux_result):
    """Extract the index metrics for a lane from a demultiplexing result."""
    return demux_result["IndexMetrics"][0]


def get_number_of_lanes_for_flow_cell(stats_data) -> int:
    """Extract the number of lanes from the stats data."""
    return len(stats_data["ReadInfosForLanes"])


def get_flow_cell_name(stats_data) -> str:
    """Extract the flow cell name from the stats data."""
    return stats_data["Flowcell"]


def get_sample_id(demux_result) -> str:
    """Extract the sample id from a demultiplexing result."""
    return demux_result["SampleId"]


def get_number_of_reads_for_sample_in_lane(demux_result) -> int:
    """Extract the number of reads for a sample in a lane."""
    return demux_result["NumberReads"]


def get_lane_number(conversion_result) -> int:
    """Extract the lane number from a conversion result."""
    return conversion_result["LaneNumber"]


def get_yield_q30(lane_read_metrics) -> int:
    """Extract the yield Q30 from the read metrics."""
    return lane_read_metrics["YieldQ30"]


def get_lane_yield_in_bases(conversion_result) -> int:
    """Extract the yield from the read metrics."""
    return conversion_result["Yield"]


def get_total_clusters_passing_filter(conversion_result) -> int:
    """Extract the total clusters passing the filter from the conversion result."""
    return conversion_result["TotalClustersPF"]


def get_total_raw_clusters(conversion_result) -> int:
    """Extract the total number of clusters initially generated, regardless of quality."""
    return conversion_result["TotalClustersRaw"]


def get_quality_score(read_metric) -> int:
    """Extract the sum of quality scores of all the bases from the read metrics."""
    return read_metric["QualityScoreSum"]


def get_lane_yield_q30_values(demux_result) -> List[int]:
    """Extract the yield Q30 values for the lane from the read metrics."""
    lane_read_metrics = get_read_metrics(demux_result)
    return [get_yield_q30(metric) for metric in lane_read_metrics]


def get_yield_values(demux_result) -> List[int]:
    lane_read_metrics = get_read_metrics(demux_result)
    return [get_lane_yield_in_bases(metric) for metric in lane_read_metrics]


def get_lane_read_quality_score_values(demux_result) -> List[int]:
    """Extract the quality score values for the lane from the read metrics."""
    lane_read_metrics = get_read_metrics(demux_result)
    return [get_quality_score(read_metric) for read_metric in lane_read_metrics]


def get_perfect_reads_for_sample_in_lane(demux_result) -> int:
    """Extract the number of perfect reads for the lane from the read metrics."""
    lane_index_metrics = get_index_metrics(demux_result)
    counts = lane_index_metrics["MismatchCounts"]
    return int(counts.get("0", 0))
