from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, field_validator

from cg.constants import SexOptions
from cg.exc import NfSampleSheetError
from cg.models.nf_analysis import WorkflowParameters
from cg.models.qc_metrics import QCMetrics


def convert_sex(plink_sex: float) -> SexOptions:
    if plink_sex == 2.0:
        return SexOptions.FEMALE
    elif plink_sex == 1.0:
        return SexOptions.MALE
    elif plink_sex == 0.0:
        return SexOptions.UNKNOWN
    else:
        raise NotImplementedError


class NalloQCMetrics(QCMetrics):
    """Nallo QC metrics."""

    avg_sequence_length: float | None
    coverage_bases: float | None
    median_coverage: float | None
    percent_duplicates: float | None
    sex: Annotated[SexOptions, BeforeValidator(convert_sex)]


class NalloSampleSheetEntry(BaseModel):
    """Nallo sample model is used when building the sample sheet."""

    project: str
    sample: str
    read_file: Path
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
                self.read_file,
                self.family_id,
                self.paternal_id,
                self.maternal_id,
                self.sex,
                self.phenotype,
            ]
        ]

    @field_validator("read_file")
    @classmethod
    def read_file_exists(cls, bam_path: Path) -> Path:
        """Verify that bam files exist."""
        if not bam_path.is_file():
            raise NfSampleSheetError(f"Bam file does not exist: {str(bam_path)}")
        return bam_path


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


class NalloParameters(WorkflowParameters):
    """Model for Nallo parameters."""

    filter_variants_hgnc_ids: str
