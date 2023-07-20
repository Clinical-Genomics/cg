from typing import List

from pydantic.v1 import BaseModel, validator


class NextflowSample(BaseModel):
    """Nextflow samplesheet model.

    Attributes:
        sample: sample name, corresponds to case_id
        fastq_r1: list of all fastq read1 files corresponding to sample
        fastq_r2: list of all fastq read2 files corresponding to sample
    """

    sample: str
    fastq_r1: List[str]
    fastq_r2: List[str]

    @validator("fastq_r2")
    def fastq1_fastq2_len_match(cls, value: List[str], values: dict) -> str:
        """Verify that the number of fastq files is the same for R1 and R2."""
        assert len(value) == len(values.get("fastq_r1")) or len(value) == 0
        return "Length of fastq_r1 and fastq_r2 do not match"
