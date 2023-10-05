from pydantic import BaseModel, Field

from cg.constants.bcl_convert_metrics import (
    BclConvertDemuxMetricsColumnNames,
    BclConvertQualityMetricsColumnNames,
)


class BclConvertQualityMetrics(BaseModel):
    """Model for the BCL Convert quality metrics."""

    lane: int = Field(..., alias=BclConvertQualityMetricsColumnNames.LANE.value)
    sample_internal_id: str = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.SAMPLE_INTERNAL_ID.value
    )
    mean_quality_score_q30: float = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.MEAN_QUALITY_SCORE_Q30.value
    )
    q30_bases_percent: float = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.Q30_BASES_PERCENT.value
    )


class BclConvertDemuxMetrics(BaseModel):
    """Model for the BCL Convert demultiplexing metrics."""

    lane: int = Field(..., alias=BclConvertDemuxMetricsColumnNames.LANE.value)
    sample_internal_id: str = Field(
        ..., alias=BclConvertDemuxMetricsColumnNames.SAMPLE_INTERNAL_ID.value
    )
    read_pair_count: int = Field(..., alias=BclConvertDemuxMetricsColumnNames.READ_PAIR_COUNT.value)
