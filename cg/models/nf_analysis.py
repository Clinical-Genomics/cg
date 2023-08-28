from pathlib import Path
from typing import List, Optional

from pydantic.v1 import BaseModel, FilePath, conlist, validator

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


class FileDeliverable(BaseModel):
    """Specification for a general deliverables file."""

    id: str
    format: str
    path: FilePath
    path_index: Optional[FilePath]
    step: str
    tag: str

    @validator("path", "path_index")
    def convert_path_to_string(cls, file_path):
        if file_path and isinstance(file_path, Path):
            return str(file_path)
        return file_path


class PipelineDeliverables(BaseModel):
    """Specification for pipeline deliverables."""

    files: List[FileDeliverable]
