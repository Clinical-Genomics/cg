from pathlib import Path
from typing import Optional, Union

from pydantic.v1 import BaseModel, Field

from cg.constants.constants import Strandedness
from cg.models.analysis import AnalysisModel
from cg.models.nf_analysis import NextflowSampleSheetEntry, PipelineParameters


class RnafusionQCMetrics(BaseModel):
    """RNAfusion QC metrics."""

    after_filtering_gc_content: Optional[float]
    after_filtering_q20_rate: Optional[float]
    after_filtering_q30_rate: Optional[float]
    after_filtering_read1_mean_length: Optional[float]
    before_filtering_total_reads: Optional[float]
    bias_5_3: Optional[float]
    pct_adapter: Optional[float]
    pct_mrna_bases: Optional[float]
    pct_ribosomal_bases: Optional[float]
    pct_surviving: Optional[float]
    pct_duplication: Optional[float]
    reads_aligned: Optional[float]
    uniquely_mapped_percent: Optional[float]


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
    fusioninspector_filter: bool = False
    fusionreport_filter: bool = False
    pizzly: bool = False
    squid: bool = False
    starfusion: bool = True
    trim: bool = False
    trim_tail: int = 50


class CommandArgs(BaseModel):
    """Model for arguments and options supported."""

    log: Optional[Union[str, Path]]
    resume: Optional[bool]
    profile: Optional[str]
    stub: Optional[bool]
    config: Optional[Union[str, Path]]
    name: Optional[str]
    revision: Optional[str]
    wait: Optional[str]
    id: Optional[str]
    with_tower: Optional[bool]
    use_nextflow: Optional[bool]
    compute_env: Optional[str]
    work_dir: Optional[Union[str, Path]]
    params_file: Optional[Union[str, Path]]


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
