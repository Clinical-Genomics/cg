from pydantic import BaseModel, Field

from cg.constants.metrics import DemuxMetricsColumnNames, QualityMetricsColumnNames


class SequencingQualityMetrics(BaseModel):
    """Model for the BCL Convert quality metrics."""

    lane: int = Field(..., alias=QualityMetricsColumnNames.LANE)
    sample_internal_id: str = Field(..., alias=QualityMetricsColumnNames.SAMPLE_INTERNAL_ID)
    mean_quality_score_q30: float = Field(
        ..., alias=QualityMetricsColumnNames.MEAN_QUALITY_SCORE_Q30
    )
    quality_score_sum: int = Field(..., alias=QualityMetricsColumnNames.QUALITY_SCORE_SUM)
    q30_bases_percent: float = Field(..., alias=QualityMetricsColumnNames.Q30_BASES_PERCENT)
    yield_: int = Field(..., alias=QualityMetricsColumnNames.YIELD)
    yield_q30: int = Field(..., alias=QualityMetricsColumnNames.YIELD_Q30)


class DemuxMetrics(BaseModel):
    """Model for the BCL Convert demultiplexing metrics."""

    lane: int = Field(..., alias=DemuxMetricsColumnNames.LANE)
    sample_internal_id: str = Field(..., alias=DemuxMetricsColumnNames.SAMPLE_INTERNAL_ID)
    read_pair_count: int = Field(..., alias=DemuxMetricsColumnNames.READ_PAIR_COUNT)
