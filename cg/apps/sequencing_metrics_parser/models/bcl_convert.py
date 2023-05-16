from pydantic import BaseModel, BaseConfig, Field
import xml.etree.ElementTree as ET


class BclConvertQualityMetrics(BaseModel):
    """Model for the BCL Convert quality metrics"""

    lane: int
    sample_internal_id: str
    read_pair_number: int
    yield_bases: int
    yield_q30_bases: int
    quality_score_sum: int
    mean_quality_score_q30: float
    q30_bases_percent: float


class BclConvertDemuxMetrics(BaseModel):
    """Model for the BCL Convert demultiplexing metrics."""

    lane: int
    sample_internal_id: str
    sample_project: str
    read_pair_count: int
    perfect_index_reads_count: int
    perfect_index_reads_percent: float
    one_mismatch_index_reads_count: int
    two_mismatch_index_reads_count: int


class BclConvertAdapterMetrics(BaseModel):
    """Model for the BCL Convert adapter metrics."""

    lane: int
    sample_internal_id: str
    sample_project: str
    read_number: int
    sample_bases: int


class BclConvertSampleSheet(BaseModel):
    """Model for the BCL Convert sample sheet."""

    flow_cell_name: str
    lane: int
    sample_internal_id: str
    sample_name: str
    control: str
    sample_project: str


class CustomConfig(BaseConfig):
    arbitrary_types_allowed = True


class BclConvertRunInfo(BaseModel):
    """Model for the BCL convert run info file."""

    tree: ET.ElementTree

    class Config(CustomConfig):
        pass
