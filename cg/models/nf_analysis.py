import collections
from typing import List

from pydantic.v1 import BaseModel, validator

from cg.constants.nextflow import DELIVER_FILE_HEADERS


class PipelineParameters(BaseModel):
    clusterOptions: str
    priority: str


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
    def fastq_forward_reverse_length_match(cls, value: List[str], values: dict) -> str:
        """Verify that the number of fastq files is the same for R1 and R2."""
        assert len(value) == len(values.get("fastq_r1")) or len(value) == 0
        return "Length of fastq_r1 and fastq_r2 do not match"


class NextflowDeliverables(BaseModel):
    """Nextflow deliverables model

    Attributes:
        deliverables: dictionary containing format, path, path_index, step, tag and id keys.
    """

    deliverables: dict

    @validator("deliverables")
    def headers(cls, v: dict) -> None:
        """Validate header format."""
        if collections.Counter(list(v.keys())) != collections.Counter(DELIVER_FILE_HEADERS):
            raise ValueError(
                f"Headers are not matching the standard header format: {DELIVER_FILE_HEADERS}"
            )
        for key, value in v.items():
            if not value and key != "path_index":
                raise ValueError("An entry other than path_index is empty!")
