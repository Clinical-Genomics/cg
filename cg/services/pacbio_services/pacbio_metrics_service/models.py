from pydantic import BaseModel, Field

from cg.constants.pacbio import CCSAttributeIDs


class HiFiMetrics(BaseModel):
    """Model for the HiFi metrics."""

    reads: int = Field(..., alias=CCSAttributeIDs.NUMBER_OF_READS)
    yield_: int = Field(..., alias=CCSAttributeIDs.TOTAL_NUMBER_OF_BASES)
    mean_read_length: int = Field(..., alias=CCSAttributeIDs.MEAN_READ_LENGTH)
    median_read_length: int = Field(..., alias=CCSAttributeIDs.MEDIAN_READ_LENGTH)
    rean_length_n50: int = Field(..., alias=CCSAttributeIDs.READ_LENGTH_N50)
    median_read_quality: str = Field(..., alias=CCSAttributeIDs.MEDIAN_ACCURACY)
    percent_q30: float = Field(..., alias=CCSAttributeIDs.PERCENT_Q30)
