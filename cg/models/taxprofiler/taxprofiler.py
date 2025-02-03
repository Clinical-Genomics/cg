from pathlib import Path

from pydantic import Field

from cg.constants.sequencing import SequencingPlatform
from cg.models.nf_analysis import NextflowSampleSheetEntry, WorkflowParameters
from cg.models.qc_metrics import QCMetrics


class TaxprofilerQCMetrics(QCMetrics):
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
    """Taxprofiler parameters."""


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
