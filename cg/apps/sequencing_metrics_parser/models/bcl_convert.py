from pydantic.v1 import BaseModel, BaseConfig, Field
from cg.constants.bcl_convert_metrics import (
    BclConvertQualityMetricsColumnNames,
    BclConvertDemuxMetricsColumnNames,
    BclConvertAdapterMetricsColumnNames,
)
from cg.constants.demultiplexing import SampleSheetNovaSeq6000Sections


class BclConvertQualityMetrics(BaseModel):
    """Model for the BCL Convert quality metrics."""

    lane: int = Field(..., alias=BclConvertQualityMetricsColumnNames.LANE.value)
    sample_internal_id: str = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.SAMPLE_INTERNAL_ID.value
    )
    read_pair_number: int = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.READ_PAIR_NUMBER.value
    )
    yield_bases: int = Field(..., alias=BclConvertQualityMetricsColumnNames.YIELD_BASES.value)
    yield_q30_bases: int = Field(..., alias=BclConvertQualityMetricsColumnNames.YIELD_Q30.value)
    quality_score_sum: int = Field(
        ..., alias=BclConvertQualityMetricsColumnNames.QUALITY_SCORE_SUM.value
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
    perfect_index_reads_count: int = Field(
        ..., alias=BclConvertDemuxMetricsColumnNames.PERFECT_INDEX_READS_COUNT.value
    )
    perfect_index_reads_percent: float = Field(
        ..., alias=BclConvertDemuxMetricsColumnNames.PERFECT_INDEX_READS_PERCENT.value
    )
    one_mismatch_index_reads_count: int = Field(
        ..., alias=BclConvertDemuxMetricsColumnNames.ONE_MISMATCH_INDEX_READS_COUNT.value
    )
    two_mismatch_index_reads_count: int = Field(
        ..., alias=BclConvertDemuxMetricsColumnNames.TWO_MISMATCH_INDEX_READS_COUNT.value
    )


class BclConvertAdapterMetrics(BaseModel):
    """Model for the BCL Convert adapter metrics."""

    lane: int = Field(..., alias=BclConvertAdapterMetricsColumnNames.LANE.value)
    sample_internal_id: str = Field(
        ..., alias=BclConvertAdapterMetricsColumnNames.SAMPLE_INTERNAL_ID.value
    )
    read_number: int = Field(..., alias=BclConvertAdapterMetricsColumnNames.READ_NUMBER.value)
    sample_bases: int = Field(..., alias=BclConvertAdapterMetricsColumnNames.SAMPLE_BASES.value)


class BclConvertSampleSheetData(BaseModel):
    """Model for the BCL Convert sample sheet."""

    flow_cell_name: str = Field(..., alias=SampleSheetNovaSeq6000Sections.Data.FLOW_CELL_ID.value)
    lane: int = Field(..., alias=SampleSheetNovaSeq6000Sections.Data.LANE.value)
    sample_internal_id: str = Field(
        ..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_INTERNAL_ID_BCLCONVERT.value
    )
    sample_name: str = Field(..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_NAME.value)
    control: str = Field(..., alias=SampleSheetNovaSeq6000Sections.Data.CONTROL.value)


class CustomConfig(BaseConfig):
    arbitrary_types_allowed = True
