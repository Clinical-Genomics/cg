from typing import List, Optional
from pydantic import BaseModel, Field


class ReadMetric(BaseModel):
    """Metrics for a read for a sample in a tile on a lane."""

    yield_: int = Field(..., alias="Yield", ge=0)
    yield_q30: int = Field(..., alias="YieldQ30", ge=0)
    quality_score_sum: int = Field(..., alias="QualityScoreSum", ge=0)


class DemuxResult(BaseModel):
    """Metrics for a sample in a tile in a lane."""

    sample_id: str = Field(..., alias="SampleId", min_length=1)
    number_reads: int = Field(..., alias="NumberReads", ge=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    read_metrics: List[ReadMetric] = Field(..., alias="ReadMetrics")


class Undetermined(BaseModel):
    """Metrics for undetermined reads for a tile in a lane."""

    number_reads: int = Field(..., alias="NumberReads", ge=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    read_metrics: List[ReadMetric] = Field(..., alias="ReadMetrics")


class ConversionResult(BaseModel):
    """Result of the conversion process for a tile in a lane."""

    lane_number: int = Field(..., alias="LaneNumber", gt=0)
    demux_results: List[DemuxResult] = Field(..., alias="DemuxResults")
    undetermined: Optional[Undetermined] = Field(None, alias="Undetermined")


class SampleLaneTileMetrics(BaseModel):
    """Metrics for samples in a lane and tile on a flow cell from a bcl2fastq run."""

    flow_cell_name: str = Field(..., alias="Flowcell", min_length=1)
    conversion_results: List[ConversionResult] = Field(..., alias="ConversionResults")


class SampleLaneMetrics(BaseModel):
    """Metrics for a sample in a lane from a bcl2fastq run."""

    flow_cell_name: str
    lane: int
    sample_id: str
    total_reads: int
    total_yield: int
    total_yield_q30: int
    total_quality_score: int
