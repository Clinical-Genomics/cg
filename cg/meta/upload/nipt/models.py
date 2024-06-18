from pydantic import BaseModel


class StatinaUploadFiles(BaseModel):
    result_file: str
    multiqc_report: str | None = None
    segmental_calls: str | None = None


class SequencingRunQ30AndReads(BaseModel):
    """Summaries for Q30 and reads of a sequencing run."""

    total_reads_on_flow_cell: int
    average_q30_across_samples: float

    def passes_read_threshold(self, threshold: int) -> bool:
        """Check if the number of reads is above a threshold."""
        return self.total_reads_on_flow_cell >= threshold

    def passes_q30_threshold(self, threshold: float) -> bool:
        """Check if the Q30 is above a threshold."""
        return self.average_q30_across_samples >= threshold
