from datetime import datetime

from pydantic import BaseModel, Field

from cg.constants import FlowCellStatus
from cg.constants.devices import DeviceType
from cg.constants.metrics import DemuxMetricsColumnNames, QualityMetricsColumnNames
from cg.constants.sequencing import Sequencers


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


class IlluminaFlowCellDTO(BaseModel):
    """Data transfer object for Illumina flow cell."""

    internal_id: str
    type: DeviceType
    model: str

    class Config:
        arbitrary_types_allowed = True


class IlluminaSequencingRunDTO(BaseModel):
    """Data transfer object for IlluminaSequencingRun."""

    type: DeviceType
    sequencer_type: Sequencers | None
    sequencer_name: str | None
    data_availability: FlowCellStatus | None
    archived_at: datetime | None
    has_backup: bool | None
    total_reads: int | None
    total_undetermined_reads: int | None
    percent_undetermined_reads: float | None
    percent_q30: float | None
    mean_quality_score: float | None
    total_yield: int | None
    yield_q30: int | None
    cycles: int | None
    demultiplexing_software: str | None
    demultiplexing_software_version: str | None
    sequencing_started_at: datetime | None
    sequencing_completed_at: datetime | None
    demultiplexing_started_at: datetime | None
    demultiplexing_completed_at: datetime | None

    class Config:
        arbitrary_types_allowed = True


class IlluminaSampleSequencingMetricsDTO(BaseModel):
    """Data transfer object for IlluminaSampleSequencingMetrics."""

    sample_id: str
    type: DeviceType
    flow_cell_lane: int
    total_reads_in_lane: int
    base_passing_q30_percent: float
    base_mean_quality_score: float
    yield_: int
    yield_q30: float
    created_at: datetime

    class Config:
        arbitrary_types_allowed = True
