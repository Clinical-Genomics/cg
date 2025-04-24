"""Module for the data transfer models for Illumina."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from cg.constants import SequencingRunDataAvailability
from cg.constants.devices import DeviceType
from cg.constants.sequencing import Sequencers
from cg.utils.calculations import fraction_to_percent


class IlluminaFlowCellDTO(BaseModel):
    """Data transfer object for Illumina flow cell."""

    internal_id: str
    type: DeviceType
    model: str | None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("model")
    def validate_model(cls, model: str) -> str:
        """Validate the model."""
        if model not in ["10B", "25B", "1.5B", "S1", "S2", "S4", "SP", None]:
            raise ValueError(f"Invalid Flow cell model detected: {model}")
        return model


class IlluminaSequencingRunDTO(BaseModel):
    """Data transfer object for IlluminaSequencingRun."""

    type: DeviceType
    sequencer_type: Sequencers | None
    sequencer_name: str | None
    data_availability: SequencingRunDataAvailability | None
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

    @field_validator("percent_undetermined_reads", "percent_q30", mode="before")
    def validate_percent_fields(cls, value: float | None) -> float | None:
        if value is not None:
            return fraction_to_percent(value)
        return value

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)


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

    @field_validator("base_passing_q30_percent", mode="before")
    def validate_percent_fields(cls, value: float | None) -> float | None:
        if value is not None:
            return fraction_to_percent(value)
        return value

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)
