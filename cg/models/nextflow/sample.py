from pydantic import BaseModel, validator


class NextflowSample(BaseModel):
    """Nextflow samplesheet model

    Attributes:
        sample: sample name, corresponds to case_id
        fastq_r1: list of all fastq read1 files corresponding to case_id
        fastq_r2: list of all fastq read2 files corresponding to case_id
    """

    sample: str
    fastq_r1: list
    fastq_r2: list

    @validator("fastq1")
    def fastq1_fastq2_len_match(cls, value: list, values: dict) -> str:
        assert len(value) == len(values.get("fastq_r2")) or len(values.get("fastq_r2")) == 0
        return value
