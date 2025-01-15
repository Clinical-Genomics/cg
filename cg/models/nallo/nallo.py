from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, conlist, field_validator

from cg.exc import NfSampleSheetError


class NalloSampleSheetEntry(BaseModel):
    """Nallo sample model is used when building the sample sheet."""

    project: str
    sample: str
    bam_unmapped_read_paths: conlist(Path)
    family_id: str
    paternal_id: str
    maternal_id: str
    sex: int
    phenotype: int

    @property
    def reformat_sample_content(self) -> list[list[str]]:
        """Reformat sample sheet content as a list of lists, where each list represents a line in the final file."""
        return [
            [
                self.project,
                self.sample,
                self.bam_unmapped_read_paths,
                self.family_id,
                self.paternal_id,
                self.maternal_id,
                self.sex,
                self.phenotype,
            ]
        ]

    @field_validator("bam_unmapped_read_paths")
    @classmethod
    def unmapped_bam_file_exists(cls, bam_paths: list[Path]) -> list[Path]:
        """Verify that bam files exist."""
        for bam_path in bam_paths:
            if not bam_path.is_file():
                raise NfSampleSheetError(f"Bam file does not exist: {str(bam_path)}")
        return bam_paths


class NalloSampleSheetHeaders(StrEnum):
    project: str = "project"
    sample: str = "sample"
    file: str = "file"
    family_id: str = "family_id"
    paternal_id: str = "paternal_id"
    maternal_id: str = "maternal_id"
    sex: str = "sex"
    phenotype: str = "phenotype"

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda header: header.value, cls))
