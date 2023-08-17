import collections
from typing import List

from pydantic.v1 import BaseModel, conlist, validator

from cg.constants.nextflow import DELIVER_FILE_HEADERS
from cg.exc import SampleSheetError


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
    fastq_forward: conlist(str, min_items=1)
    fastq_reverse: conlist(str, min_items=1)

    @validator("fastq_reverse")
    def fastq_forward_reverse_length_match(
        cls, fastq_reverse: List[str], values: dict
    ) -> List[str]:
        """Verify that the number of fastq forward files is the same as for the reverse."""
        if len(fastq_reverse) != len(values.get("fastq_forward")):
            raise SampleSheetError("Fastq file length for forward and reverse do not match")
        return fastq_reverse


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
