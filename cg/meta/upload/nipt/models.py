from typing import Optional
from pydantic import BaseModel


class StatinaUploadFiles(BaseModel):
    result_file: str
    multiqc_report: Optional[str]
    segmental_calls: Optional[str]


class FlowCellQ30AndReads:
    """Summary of a flow cell"""

    reads: int
    q30: float

    def __init__(self, reads: int, q30: float):
        self.reads = reads
        self.q30 = q30

    def reads_above_threshold(self, threshold: int) -> bool:
        """Check if the number of reads is above a threshold"""
        return self.reads >= threshold

    def q30_above_threshold(self, threshold: float) -> bool:
        """Check if the Q30 is above a threshold"""
        return self.q30 >= threshold
