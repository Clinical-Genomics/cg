from typing import Optional
from pydantic.v1 import BaseModel


class StatinaUploadFiles(BaseModel):
    result_file: str
    multiqc_report: Optional[str]
    segmental_calls: Optional[str]


class FlowCellQ30AndReads(BaseModel):
    """Summary of a flow cell"""

    reads: int
    q30: float

    def reads_above_threshold(self, threshold: int) -> bool:
        """Check if the number of reads is above a threshold"""
        return self.reads >= threshold

    def q30_above_threshold(self, threshold: float) -> bool:
        """Check if the Q30 is above a threshold"""
        return self.q30 >= threshold
