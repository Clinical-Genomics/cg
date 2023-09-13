from typing import List, Optional
from pydantic import BaseModel, Field


class ReadMetric(BaseModel):
    """
    Represents a set of metrics generated by bcl2fastq for a read in the sequencing process.
    """

    yield_: int = Field(..., alias="Yield", ge=0)
    yield_q30: int = Field(..., alias="YieldQ30", ge=0)
    quality_score_sum: int = Field(..., alias="QualityScoreSum", ge=0)


class DemuxResult(BaseModel):
    """
    Represents the result of the bcl2fastq demultiplexing process for a given sample.
    """

    sample_id: str = Field(..., alias="SampleId", min_length=1)
    number_reads: int = Field(..., alias="NumberReads", ge=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    read_metrics: List[ReadMetric] = Field(..., alias="ReadMetrics")


class Undetermined(BaseModel):
    number_reads: int = Field(..., alias="NumberReads", ge=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    read_metrics: List[ReadMetric] = Field(..., alias="ReadMetrics")


class ConversionResult(BaseModel):
    """
    Represents the result of the conversion process for a given lane as generated by
    the bcl2fastq demultiplexing software.
    """

    lane_number: int = Field(..., alias="LaneNumber", gt=0)
    demux_results: List[DemuxResult] = Field(..., alias="DemuxResults")
    undetermined: Optional[Undetermined] = Field(None, alias="Undetermined")


class SampleLaneTileMetrics(BaseModel):
    """
    Represents a set of sequencing metrics for a bcl2fastq run per sample, lane and tile on a flow cell.
    """

    flow_cell_name: str = Field(..., alias="Flowcell", min_length=1)
    conversion_results: List[ConversionResult] = Field(..., alias="ConversionResults")


class SampleLaneMetrics(BaseModel):
    """
    Aggregated metrics per sample and lane from a bcl2fastq run.
    """

    flow_cell_name: str
    lane_number: int
    sample_id: str
    total_reads: int
    total_yield: int
    total_yield_q30: int
    total_quality_score: int
