"""Rnafusion quality control metrics model."""
from typing import Optional

from pydantic import BaseModel


class RnafusionQCMetrics(BaseModel):
    """RNAfusion QC metrics."""

    after_filtering_gc_content: Optional[float] = None
    after_filtering_q20_rate: Optional[float] = None
    after_filtering_q30_rate: Optional[float] = None
    after_filtering_read1_mean_length: Optional[float] = None
    before_filtering_total_reads: Optional[float] = None
    bias_5_3: Optional[float] = None
    pct_adapter: Optional[float] = None
    pct_mrna_bases: Optional[float] = None
    pct_ribosomal_bases: Optional[float] = None
    pct_surviving: Optional[float] = None
    pct_duplication: Optional[float] = None
    reads_aligned: Optional[float] = None
    uniquely_mapped_percent: Optional[float] = None
