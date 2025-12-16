from pathlib import Path

from pydantic import field_validator

from cg.constants.constants import GenomeVersion
from cg.constants.sample_sources import SourceType
from cg.models.nf_analysis import WorkflowParameters
from cg.models.qc_metrics import QCMetrics
from cg.utils.utils import replace_non_alphanumeric


# TODO: Move and refactor
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
