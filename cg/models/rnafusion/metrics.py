"""Rnafusion quality control metrics model."""
from typing import Optional

from pydantic.v1 import BaseModel


class RnafusionQCMetrics(BaseModel):
    """RNAfusion QC metrics."""

    after_filtering_gc_content: Optional[float]
    after_filtering_q20_rate: Optional[float]
    after_filtering_q30_rate: Optional[float]
    after_filtering_read1_mean_length: Optional[float]
    before_filtering_total_reads: Optional[float]
    bias_5_3: Optional[float]
    pct_adapter: Optional[float]
    pct_mrna_bases: Optional[float]
    pct_ribosomal_bases: Optional[float]
    pct_surviving: Optional[float]
    pct_duplication: Optional[float]
    reads_aligned: Optional[float]
    uniquely_mapped_percent: Optional[float]
