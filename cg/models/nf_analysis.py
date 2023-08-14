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
        fastq_forward: list of all fastq read1 files corresponding to sample
        fastq_reverse: list of all fastq read2 files corresponding to sample
    """

    sample: str
    fastq_forward: List[str]
    fastq_reverse: List[str]

    @validator("fastq_reverse")
    def fastq_forward_reverse_length_match(cls, fastq_reverse: List[str], values: dict) -> str:
        """Verify that the number of fastq files is the same for R1 and R2."""
        assert len(fastq_reverse) == len(values.get("fastq_forward")) or len(fastq_reverse) == 0
        return "Fastq file length for forward and reverse do not match"


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
