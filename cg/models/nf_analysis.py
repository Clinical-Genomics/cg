import collections
from pathlib import Path
from typing import List

from pydantic.v1 import BaseModel, Field, conlist, validator

from cg.constants.nextflow import DELIVER_FILE_HEADERS
from cg.exc import SampleSheetError


class PipelineParameters(BaseModel):
    clusterOptions: str = Field(..., alias="cluster_options")
    priority: str


class NextflowSampleSheetEntry(BaseModel):
    """Nextflow samplesheet model.

    Attributes:
        name: sample name, corresponds to case_id
        fastq_forward_read_paths: list of all fastq read1 file paths corresponding to sample
        fastq_reverse_read_paths: list of all fastq read2 file paths corresponding to sample
    """

    name: str
    fastq_forward_read_paths: conlist(Path, min_items=1)
    fastq_reverse_read_paths: conlist(Path, min_items=1)

    @validator("fastq_reverse_read_paths")
    def validate_complete_fastq_file_pairs(
        cls, fastq_reverse: List[str], values: dict
    ) -> List[str]:
        """Verify that the number of fastq forward files is the same as for the reverse."""
        if len(fastq_reverse) != len(values.get("fastq_forward_read_paths")):
            raise SampleSheetError("Fastq file length for forward and reverse do not match")
        return fastq_reverse

    @validator("fastq_forward_read_paths", "fastq_reverse_read_paths")
    def fastq_files_exist(cls, fastq_paths: List[str], values: dict) -> List[str]:
        """Verify that fastq files exist."""
        for fastq_path in fastq_paths:
            if not fastq_path.is_file():
                raise SampleSheetError(f"Fastq file does not exist: {str(fastq_path)}")
        return fastq_paths


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
