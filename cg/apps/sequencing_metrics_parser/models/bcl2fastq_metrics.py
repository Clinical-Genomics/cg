from typing import List, Dict
from pydantic import BaseModel, Field, validator


class IndexMetric(BaseModel):
    index_sequence: str = Field(..., alias="IndexSequence", min_length=1)
    mismatch_counts: Dict[str, int] = Field(..., alias="MismatchCounts")

    @validator("mismatch_counts", each_item=True)
    def check_non_negative(cls, value):
        if value < 0:
            raise ValueError("MismatchCounts must be non-negative")
        return value


class ReadMetric(BaseModel):
    read_number: int = Field(..., alias="ReadNumber", gt=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    yield_q30: int = Field(..., alias="YieldQ30", ge=0)
    quality_score_sum: int = Field(..., alias="QualityScoreSum", ge=0)


class DemuxResult(BaseModel):
    sample_id: str = Field(..., alias="SampleId", min_length=1)
    sample_name: str = Field(..., alias="SampleName", min_length=1)
    index_metrics: List[IndexMetric] = Field(..., alias="IndexMetrics")
    number_reads: int = Field(..., alias="NumberReads", gt=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    read_metrics: List[ReadMetric] = Field(..., alias="ReadMetrics")


class ConversionResult(BaseModel):
    lane_number: int = Field(..., alias="LaneNumber", gt=0)
    total_clusters_raw: int = Field(..., alias="TotalClustersRaw", ge=0)
    total_clusters_pf: int = Field(..., alias="TotalClustersPF", ge=0)
    yield_: int = Field(..., alias="Yield", ge=0)
    demux_results: List[DemuxResult] = Field(..., alias="DemuxResults")


class ReadInfoForLane(BaseModel):
    lane_number: int = Field(..., alias="LaneNumber", gt=0)


class Bcl2FastqSequencingMetrics(BaseModel):
    flowcell: str = Field(..., alias="Flowcell", min_length=1)
    run_number: int = Field(..., alias="RunNumber", gt=0)
    run_id: str = Field(..., alias="RunId", min_length=1)
    read_infos_for_lanes: List[ReadInfoForLane] = Field(..., alias="ReadInfosForLanes")
    conversion_results: List[ConversionResult] = Field(..., alias="ConversionResults")
