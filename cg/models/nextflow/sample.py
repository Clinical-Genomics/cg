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

    @validator("fastq_r2")
    def fastq1_fastq2_len_match(cls, value, values: dict) -> str:
        assert len(value) == len(values.get("fastq_r1")) or len(value) == 0
        return "Length of fastq_r1 and fastq_r2 do not match"
