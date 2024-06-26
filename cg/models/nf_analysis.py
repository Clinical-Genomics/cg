from pathlib import Path

from pydantic.v1 import BaseModel, Field, conlist, validator

from cg.exc import NfSampleSheetError


class WorkflowParameters(BaseModel):
    input: Path
    outdir: Path


class NfCommandArgs(BaseModel):
    """Model for arguments and options supported."""

    log: str | Path | None
    resume: bool | None
    profile: str | None
    stub: bool | None
    config: str | Path | None
    name: str | None
    revision: str | None
    wait: str | None
    id: str | None
    with_tower: bool | None
    use_nextflow: bool | None
    compute_env: str | None
    work_dir: str | Path | None
    params_file: str | Path | None


class NextflowSampleSheetEntry(BaseModel):
    """Nextflow sample sheet model.

    Attributes:
        name: sample name, or case id
        fastq_forward_read_paths: list of all fastq read1 file paths corresponding to sample
        fastq_reverse_read_paths: list of all fastq read2 file paths corresponding to sample
    """

    name: str
    fastq_forward_read_paths: conlist(Path, min_items=1)
    fastq_reverse_read_paths: conlist(Path, min_items=1)

    @validator("fastq_reverse_read_paths")
    def validate_complete_fastq_file_pairs(
        cls, fastq_reverse: list[str], values: dict
    ) -> list[str]:
        """Verify that the number of fastq forward files is the same as for the reverse."""
        if len(fastq_reverse) != len(values.get("fastq_forward_read_paths")):
            raise NfSampleSheetError("Fastq file length for forward and reverse do not match")
        return fastq_reverse

    @validator("fastq_forward_read_paths", "fastq_reverse_read_paths")
    def fastq_files_exist(cls, fastq_paths: list[str], values: dict) -> list[str]:
        """Verify that fastq files exist."""
        for fastq_path in fastq_paths:
            if not fastq_path.is_file():
                raise NfSampleSheetError(f"Fastq file does not exist: {str(fastq_path)}")
        return fastq_paths


class FileDeliverable(BaseModel):
    """Specification for a general deliverables file."""

    id: str
    format: str
    path: str
    path_index: str | None
    step: str
    tag: str

    @validator("path", "path_index", pre=True)
    def set_path_as_string(cls, file_path: str | Path) -> str | None:
        if file_path:
            return str(Path(file_path))
        return None


class WorkflowDeliverables(BaseModel):
    """Specification for workflow deliverables."""

    files: list[FileDeliverable]
