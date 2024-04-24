from enum import StrEnum
from pathlib import Path

from pydantic.v1 import validator

from cg.constants.constants import GenomeVersion, Strandedness
from cg.constants.sample_sources import SourceType
from cg.models.nf_analysis import NextflowSampleSheetEntry, WorkflowParameters
from cg.utils.utils import replace_non_alphanumeric


class TomteSampleSheetEntry(NextflowSampleSheetEntry):
    """Tomte sample model is used when building the sample sheet."""

    case_id: str
    strandedness: Strandedness

    @property
    def reformat_sample_content(self) -> list[list[str]]:
        """Reformat sample sheet content as a list of lists, where
        each list represents a line in the final file."""
        return [
            [
                self.case_id,
                self.name,
                fastq_forward_read_path,
                fastq_reverse_read_path,
                str(self.strandedness),
            ]
            for fastq_forward_read_path, fastq_reverse_read_path in zip(
                self.fastq_forward_read_paths, self.fastq_reverse_read_paths
            )
        ]


class TomteSampleSheetHeaders(StrEnum):
    case_id: str = "case"
    name: str = "sample"
    fastq_1: str = "fastq_1"
    fastq_2: str = "fastq_2"
    strandedness: str = "strandedness"

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda header: header.value, cls))


class TomteParameters(WorkflowParameters):
    """Model for Tomte parameters."""

    gene_panel_clinical_filter: Path
    tissue: str
    genome: str

    @validator("tissue", pre=True)
    def restrict_tissue_values(cls, tissue: str) -> str:
        if tissue:
            return replace_non_alphanumeric(string=tissue)
        return SourceType.UNKNOWN

    @validator("genome", pre=True)
    def restrict_genome_values(cls, genome: str) -> str:
        if genome == GenomeVersion.hg38:
            return "GRCh38"
        elif genome == GenomeVersion.hg19:
            return "GRCh37"
        