from pydantic import BaseModel


class SampleMetadata(BaseModel):
    sample_internal_id: str
    sample_name: str
    is_external_negative_control: bool
    is_internal_negative_control: bool = False
    reads: int
    target_reads: int
    percent_reads_guaranteed: int


class SamplesMetadataMetrics(BaseModel):
    samples: dict[str, SampleMetadata]
