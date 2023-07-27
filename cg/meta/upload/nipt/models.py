from typing import Optional
from pydantic.v1 import BaseModel


class StatinaUploadFiles(BaseModel):
    result_file: str
    multiqc_report: Optional[str]
    segmental_calls: Optional[str]


class FlowCellQ30AndReads(BaseModel):
    """Summary of a flow cell"""

    total_reads_on_flow_cell: int
    average_q30_across_samples: float

    def reads_above_threshold(self, threshold: int) -> bool:
        """Check if the number of reads is above a threshold"""
        return self.total_reads_on_flow_cell >= threshold

    def q30_above_threshold(self, threshold: float) -> bool:
        """Check if the Q30 is above a threshold"""
        return self.average_q30_across_samples >= threshold
