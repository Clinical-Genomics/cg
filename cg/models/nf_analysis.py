from pathlib import Path

from pydantic import BaseModel, ValidationInfo, conlist, field_validator

from cg.exc import NfSampleSheetError


class WorkflowParameters(BaseModel):
    input: Path
    outdir: Path


class NfCommandArgs(BaseModel):
    """Model for arguments and options supported."""

    log: str | Path | None = None
    resume: bool | None = None
    profile: str | None = None
    stub_run: bool | None = None
    config: str | Path | None = None
    name: str | None = None
    revision: str | None = None
    wait: str | None = None
    id: str | None = None
    with_tower: bool | None = None
    use_nextflow: bool | None = None
    compute_env: str | None = None
    work_dir: str | Path | None = None
    params_file: str | Path | None = None


class NextflowSampleSheetEntry(BaseModel):
    """Nextflow sample sheet model.

    Attributes:
        name: sample name, or case id
        fastq_forward_read_paths: list of all fastq read1 file paths corresponding to sample
        fastq_reverse_read_paths: list of all fastq read2 file paths corresponding to sample
    """

    name: str
    fastq_forward_read_paths: conlist(Path, min_length=1)
    fastq_reverse_read_paths: conlist(Path, min_length=1)

    @field_validator("fastq_reverse_read_paths")
    @classmethod
    def validate_complete_fastq_file_pairs(
        cls, fastq_reverse: list[str], info: ValidationInfo
    ) -> list[str]:
        """Verify that the number of fastq forward files is the same as for the reverse."""
        if len(fastq_reverse) != len(info.data.get("fastq_forward_read_paths")):
            raise NfSampleSheetError("Fastq file length for forward and reverse do not match")
        return fastq_reverse

    @field_validator("fastq_forward_read_paths", "fastq_reverse_read_paths")
    @classmethod
    def fastq_files_exist(cls, fastq_paths: list[str]) -> list[str]:
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
    path_index: str | None = None
    step: str
    tag: str

    @field_validator("path", "path_index", mode="before")
    @classmethod
    def set_path_as_string(cls, file_path: str | Path) -> str | None:
        return str(Path(file_path)) if file_path else None


class WorkflowDeliverables(BaseModel):
    """Specification for workflow deliverables."""

    files: list[FileDeliverable]
