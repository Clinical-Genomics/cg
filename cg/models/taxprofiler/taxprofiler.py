from pathlib import Path

from pydantic import Field, BaseModel

from cg.constants.sequencing import SequencingPlatform
from cg.models.nf_analysis import NextflowSampleSheetEntry, PipelineParameters


class TaxprofilerQCMetrics(BaseModel):
    """Taxprofiler QC metrics."""

    after_filtering_total_reads: float | None
    reads_mapped: float | None
    before_filtering_total_reads: float | None
    paired_aligned_none: float | None


class TaxprofilerParameters(PipelineParameters):
    """Model for Taxprofiler parameters."""

    input: Path = Field(..., alias="sample_sheet_path")
    outdir: Path
    databases: Path
    save_preprocessed_reads: bool = True
    perform_shortread_qc: bool = True
    perform_shortread_complexityfilter: bool = True
    save_complexityfiltered_reads: bool = True
    perform_shortread_hostremoval: bool = True
    hostremoval_reference: Path
    save_hostremoval_index: bool = True
    save_hostremoval_mapped: bool = True
    save_hostremoval_unmapped: bool = True
    perform_runmerging: bool = True
    run_kraken2: bool = True
    kraken2_save_reads: bool = True
    kraken2_save_readclassification: bool = True
    run_krona: bool = True
    run_profile_standardisation: bool = True


class TaxprofilerSampleSheetEntry(NextflowSampleSheetEntry):
    """Taxprofiler sample model is used when building the sample sheet."""

    instrument_platform: SequencingPlatform
    run_accession: str
    fasta: str

    @staticmethod
    def headers() -> list[str]:
        """Return sample sheet headers."""
        return [
            "sample",
            "run_accession",
            "instrument_platform",
            "fastq_1",
            "fastq_2",
            "fasta",
        ]

    def reformat_sample_content(self) -> list[list[str]]:
        """Reformat sample sheet content as a list of list, where each list represents a line in the final file."""
        return [
            [
                self.name,
                self.run_accession,
                self.instrument_platform,
                fastq_forward_read_path,
                fastq_reverse_read_path,
                self.fasta,
            ]
            for fastq_forward_read_path, fastq_reverse_read_path in zip(
                self.fastq_forward_read_paths, self.fastq_reverse_read_paths
            )
        ]
