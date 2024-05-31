from pydantic import BaseModel, Field


class HiFiMetrics(BaseModel):
    """Model for the HiFi metrics."""

    reads: int = Field(..., alias="ccs2.number_of_ccs_reads")
    yield_: int = Field(..., alias="ccs2.total_number_of_ccs_bases")
    mean_read_length: int = Field(..., alias="ccs2.mean_ccs_readlength")
    median_read_length: int = Field(..., alias="ccs2.median_ccs_readlength")
    rean_length_n50: int = Field(..., alias="ccs2.ccs_readlength_n50")
    median_read_quality: str = Field(..., alias="ccs2.median_accuracy")
    percent_q30: float = Field(..., alias="ccs2.percent_ccs_bases_q30")
