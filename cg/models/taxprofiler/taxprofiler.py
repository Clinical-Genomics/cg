from pathlib import Path
from pydantic.v1 import BaseModel, Field

from cg.constants.sequencing import SequencingPlatform
from cg.models.nf_analysis import NextflowSampleSheetEntry, WorkflowParameters


class TaxprofilerQCMetrics(BaseModel):
    """Taxprofiler QC metrics."""

    after_filtering_gc_content: float
    after_filtering_read1_mean_length: float
    after_filtering_read2_mean_length: float
    after_filtering_total_reads: float
    average_length: float
    pct_duplication: float
    raw_total_sequences: float
    reads_mapped: float


class TaxprofilerParameters(WorkflowParameters):
    """Model for Taxprofiler parameters."""

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
    kraken2_save_readclassifications: bool = True
    run_bracken: bool = True
    run_centrifuge: bool = True
    centrifuge_save_reads: bool = True
    run_krona: bool = True
    run_profile_standardisation: bool = True
    clusterOptions: str = Field(..., alias="cluster_options")
    priority: str


class TaxprofilerSampleSheetEntry(NextflowSampleSheetEntry):
    """Taxprofiler sample model is used when building the sample sheet."""

    instrument_platform: SequencingPlatform
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
        reformatted_content = []
        for run_accession, (forward_path, reverse_path) in enumerate(
            zip(self.fastq_forward_read_paths, self.fastq_reverse_read_paths), 1
        ):
            line = [
                self.name,
                run_accession,
                self.instrument_platform,
                forward_path,
                reverse_path,
                self.fasta,
            ]
            reformatted_content.append(line)
        return reformatted_content
