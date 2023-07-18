from typing import List, Dict
from pydantic import BaseModel, Field, validator


class IndexMetric(BaseModel):
    """
    Represents a metric generated by bcl2fastq for a specific index sequence in the demultiplexing process.
    Each instance of this class includes the index sequence itself and a dictionary
    mapping mismatch counts to their frequencies.

    Fields:
    - mismatch_counts: A dictionary mapping mismatch counts (as strings) to their
      respective frequencies.
    """

    mismatch_counts: Dict[str, int] = Field(..., alias="MismatchCounts")

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("mismatch_counts", each_item=True)
    def check_non_negative(cls, value):
        if value < 0:
            raise ValueError("MismatchCounts must be non-negative")
        return value


class ReadMetric(BaseModel):
    """
    Represents a set of metrics generated by bcl2fastq for a read in the sequencing process.

    Fields:
    - read_number: The read number this metric pertains to.
    - yield_: The yield from this read.
    - yield_q30: The yield with quality score greater than or equal to 30 from this read.
    - quality_score_sum: The sum of quality scores from this read.
    """

    read_number: int = Field(..., alias="ReadNumber", gt=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    yield_q30: int = Field(..., alias="YieldQ30", ge=0)
    quality_score_sum: int = Field(..., alias="QualityScoreSum", ge=0)


class DemuxResult(BaseModel):
    """
    Represents the result of the bcl2fastq demultiplexing process for a given sample.

    Fields:
    - sample_id: The unique identifier for the sample.
    - sample_name: The name of the sample.
    - index_metrics: A list of metrics for each index sequence related to this sample.
    - number_reads: The total number of reads for this sample.
    - yield_: The total yield from this sample.
    - read_metrics: A list of read metrics for each read related to this sample.
    """

    sample_id: str = Field(..., alias="SampleId", min_length=1)
    sample_name: str = Field(..., alias="SampleName", min_length=1)
    index_metrics: List[IndexMetric] = Field(..., alias="IndexMetrics")
    number_reads: int = Field(..., alias="NumberReads", gt=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    read_metrics: List[ReadMetric] = Field(..., alias="ReadMetrics")


class ConversionResult(BaseModel):
    """
    Represents the result of the conversion process for a given lane as generated by
    the bcl2fastq demultiplexing software.

    Fields:
    - lane_number: The number of the lane this result pertains to.
    - yield_: The total yield from this lane.
    - demux_results: A list of demultiplexing results for each sample in this lane.
    """

    lane_number: int = Field(..., alias="LaneNumber", gt=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    demux_results: List[DemuxResult] = Field(..., alias="DemuxResults")


class ReadInfoForLane(BaseModel):
    """
    Represents basic information for a given lane.

    Fields:
    - lane_number: The number of the lane.
    """

    lane_number: int = Field(..., alias="LaneNumber", gt=0)


class Bcl2FastqSampleLaneTileMetrics(BaseModel):
    """
    Represents a set of sequencing metrics for a bcl2fastq run per sample, lane and tile on a flow cell.

    Fields:
    - flowcell: The identifier for the flowcell used in this run.
    - read_infos_for_lanes: A list of basic information for each lane in this run.
    - conversion_results: A list of conversion results for each lane in this run.
    """

    flow_cell_name: str = Field(..., alias="Flowcell", min_length=1)
    read_infos_for_lanes: List[ReadInfoForLane] = Field(..., alias="ReadInfosForLanes")
    conversion_results: List[ConversionResult] = Field(..., alias="ConversionResults")


class Bcl2FastqSampleLaneMetrics(BaseModel):
    """
    Aggregated metrics per sample and lane from a bcl2fastq run.

     Attributes:
     - flow_cell_name (str): Name of the flow cell.
     - flow_cell_lane_number (int): Lane number within the flow cell.
     - sample_id (str): Unique identifier of the sample.
     - sample_total_reads_in_lane (int): Total number of reads for the sample in the lane.
     - sample_total_yield_in_lane (int): Total yield of bases for the sample in the lane.
     - sample_total_yield_q30_in_lane (int): Total yield of bases with Q30 quality score in the lane.
     - sample_total_quality_score_in_lane (int): Sum of quality scores for all bases in the sample reads in the lane.
    """

    flow_cell_name: str
    flow_cell_lane_number: int
    sample_id: str
    sample_total_reads_in_lane: int
    sample_total_yield_in_lane: int
    sample_total_yield_q30_in_lane: int
    sample_total_quality_score_in_lane: int
