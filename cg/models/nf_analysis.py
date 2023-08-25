@classmethod
def statuses(cls) -> Tuple:
    return tuple(status.value for status in cls)


import collections
from pathlib import Path
from typing import List, Optional, Union

from pydantic.v1 import BaseModel, FilePath, conlist, root_validator, validator

from cg import resources
from cg.constants.constants import FileFormat
from cg.constants.nextflow import DELIVER_FILE_HEADERS
from cg.exc import SampleSheetError
from cg.io.controller import ReadFile


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
    path: Path  # FilePath
    path_index: Optional[FilePath] = "'~'"
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


class RnafusionDeliverables(PipelineDeliverables):
    """Specification for pipeline deliverables."""

    @staticmethod
    def get_deliverables_template() -> List[dict]:
        """Return deliverables file template content."""
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML,
            file_path=resources.RNAFUSION_BUNDLE_FILENAMES_PATH,
        )

    @classmethod
    def get_deliverables_for_case(cls, case_id: str, case_path: Path):
        """Return RnafusionDeliverables for a given case."""
        template: List[dict] = cls.get_deliverables_template()
        files: list = []
        for file in template:
            for key, value in file.items():
                if value is None:
                    continue
                file[key] = file[key].replace("CASEID", case_id)
                file[key] = file[key].replace("PATHTOCASE", str(case_path))
            files.append(FileDeliverable(**file))
        return cls(files=files)
