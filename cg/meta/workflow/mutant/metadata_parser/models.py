from pydantic import BaseModel


class SampleMetadata(BaseModel):
    sample_internal_id: str
    sample_name: str
    reads: int
    target_reads: int
    percent_reads_guaranteed: int


class SamplesMetadataMetrics(BaseModel):
    samples: dict[str, SampleMetadata]
    internal_control: SampleMetadata
    external_control: SampleMetadata
