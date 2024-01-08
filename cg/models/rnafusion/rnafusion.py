from pathlib import Path

from pydantic.v1 import BaseModel, Field

from cg.constants.constants import Strandedness
from cg.models.analysis import AnalysisModel
from cg.models.nf_analysis import NextflowSampleSheetEntry, PipelineParameters


class RnafusionQCMetrics(BaseModel):
    """RNAfusion QC metrics."""

    after_filtering_gc_content: float | None
    after_filtering_q20_rate: float | None
    after_filtering_q30_rate: float | None
    after_filtering_read1_mean_length: float | None
    before_filtering_total_reads: float | None
    median_5prime_to_3prime_bias: float | None
    pct_adapter: float | None
    pct_mrna_bases: float | None
    pct_ribosomal_bases: float | None
    pct_surviving: float | None
    pct_duplication: float | None
    read_pairs_examined: float | None
    uniquely_mapped_percent: float | None


class RnafusionParameters(PipelineParameters):
    """Rnafusion parameters."""

    genomes_base: Path
    input: Path = Field(..., alias="sample_sheet_path")
    outdir: Path
    all: bool = False
    arriba: bool = True
    cram: str = "arriba,starfusion"
    fastp_trim: bool = True
    fusioncatcher: bool = True
    starfusion: bool = True
    trim_tail: int = 50


class CommandArgs(BaseModel):
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


class RnafusionSampleSheetEntry(NextflowSampleSheetEntry):
    """Rnafusion sample sheet model."""

    strandedness: Strandedness

    @staticmethod
    def headers() -> list[str]:
        """Return sample sheet headers."""
        return ["sample", "fastq_1", "fastq_2", "strandedness"]

    def reformat_sample_content(self) -> list[list[str]]:
        """Reformat sample sheet content as a list of list, where each list represents a line in the final file."""
        return [
            [self.name, fastq_forward_read_path, fastq_reverse_read_path, str(self.strandedness)]
            for fastq_forward_read_path, fastq_reverse_read_path in zip(
                self.fastq_forward_read_paths, self.fastq_reverse_read_paths
            )
        ]


class RnafusionAnalysis(AnalysisModel):
    """Rnafusion analysis model.

    Attributes:
        sample_metrics: retrieved QC metrics associated to a sample
    """

    sample_metrics: dict[str, RnafusionQCMetrics]
