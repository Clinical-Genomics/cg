from pydantic import BaseModel


class StatinaUploadFiles(BaseModel):
    result_file: str
    multiqc_report: str | None = None
    segmental_calls: str | None = None


class SequencingRunQ30AndReads(BaseModel):
<<<<<<< HEAD
    """Summaries for Q30 and Reads of a flow cell."""
=======
    """Summaries for Q30 and reads of a sequencing run."""
>>>>>>> 40fd81003008d18320e7dab91b461cb914aefa66

    total_reads_on_flow_cell: int
    average_q30_across_samples: float

    def passes_read_threshold(self, threshold: int) -> bool:
        """Check if the number of reads is above a threshold."""
        return self.total_reads_on_flow_cell >= threshold

    def passes_q30_threshold(self, threshold: float) -> bool:
        """Check if the Q30 is above a threshold."""
        return self.average_q30_across_samples >= threshold
