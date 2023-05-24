"""Rnafusion quality control metrics model."""
from typing import Optional

from pydantic import BaseModel


class RnafusionQCMetrics(BaseModel):
    """RNAfusion QC metrics."""

    after_filtering_gc_content: Optional[float]
    after_filtering_q20_rate: Optional[float]
    after_filtering_q30_rate: Optional[float]
    after_filtering_read1_mean_length: Optional[float]
    bias_5_3: Optional[float]
    pct_adapter: Optional[float]
    pct_mrna_bases: Optional[float]
    pct_ribosomal_bases: Optional[float]
    pct_surviving: Optional[float]
    percent_duplication: Optional[float]
    uniquely_mapped: Optional[float]
    uniquely_mapped_percent: Optional[float]
