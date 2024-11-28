from enum import StrEnum
from pathlib import Path

from pydantic import field_validator

from cg.constants.constants import GenomeVersion, Strandedness
from cg.constants.sample_sources import SourceType
from cg.models.nf_analysis import NextflowSampleSheetEntry, WorkflowParameters
from cg.models.qc_metrics import QCMetrics
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
    genome: str = GenomeVersion.HG38

    @field_validator("tissue", mode="before")
    @classmethod
    def restrict_tissue_values(cls, tissue: str | None) -> str:
        if tissue:
            return replace_non_alphanumeric(string=tissue)
        else:
            return SourceType.UNKNOWN

    @field_validator("genome", mode="before")
    @classmethod
    def restrict_genome_values(cls, genome: str) -> str:
        if genome == GenomeVersion.HG38:
            return GenomeVersion.GRCh38.value
        elif genome == GenomeVersion.HG19:
            return GenomeVersion.GRCh37.value


class TomteQCMetrics(QCMetrics):
    """Tomte QC metrics."""

    after_filtering_gc_content: float
    after_filtering_q20_rate: float
    after_filtering_q30_rate: float
    after_filtering_read1_mean_length: float
    before_filtering_total_reads: float
    median_5prime_to_3prime_bias: float
    pct_adapter: float
    pct_duplication: float
    pct_intergenic_bases: float
    pct_intronic_bases: float
    pct_mrna_bases: float
    pct_ribosomal_bases: float
    pct_surviving: float
    uniquely_mapped_percent: float
