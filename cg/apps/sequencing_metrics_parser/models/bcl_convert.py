from pydantic import BaseModel, Field

from cg.constants.bcl_convert_metrics import (
    BclConvertDemuxMetricsColumnNames,
    BclConvertQualityMetricsColumnNames,
)


class BclConvertQualityMetrics(BaseModel):
    """Model for the BCL Convert quality metrics."""

    lane: int = Field(..., alias=BclConvertQualityMetricsColumnNames.LANE)
    sample_internal_id: str = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.SAMPLE_INTERNAL_ID
    )
    mean_quality_score_q30: float = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.MEAN_QUALITY_SCORE_Q30
    )
    q30_bases_percent: float = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.Q30_BASES_PERCENT
    )


class BclConvertDemuxMetrics(BaseModel):
    """Model for the BCL Convert demultiplexing metrics."""

    lane: int = Field(..., alias=BclConvertDemuxMetricsColumnNames.LANE)
    sample_internal_id: str = Field(..., alias=BclConvertDemuxMetricsColumnNames.SAMPLE_INTERNAL_ID)
    read_pair_count: int = Field(..., alias=BclConvertDemuxMetricsColumnNames.READ_PAIR_COUNT)
