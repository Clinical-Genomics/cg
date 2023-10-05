from typing import Optional

from pydantic import BaseModel


class StatinaUploadFiles(BaseModel):
    result_file: str
    multiqc_report: Optional[str] = None
    segmental_calls: Optional[str] = None


class FlowCellQ30AndReads(BaseModel):
    """Summaries for Q30 and Reads of a flow cell."""

    total_reads_on_flow_cell: int
    average_q30_across_samples: float

    def passes_read_threshold(self, threshold: int) -> bool:
        """Check if the number of reads is above a threshold."""
        return self.total_reads_on_flow_cell >= threshold

    def passes_q30_threshold(self, threshold: float) -> bool:
        """Check if the Q30 is above a threshold."""
        return self.average_q30_across_samples >= threshold
