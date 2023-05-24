"""Rnafusion quality control metrics model."""
from typing import Optional

from pydantic import BaseModel


class RnafusionQCMetrics(BaseModel):
    """RNAfusion QC metrics."""

    uniquely_mapped: Optional[float]
    uniquely_mapped_percent: Optional[float]
    PERCENT_DUPLICATION: Optional[float]
    PCT_MRNA_BASES: Optional[float]
    PCT_RIBOSOMAL_BASES: Optional[float]
    pct_surviving: Optional[float]
    after_filtering_q20_rate: Optional[float]
    after_filtering_q30_rate: Optional[float]
    after_filtering_gc_content: Optional[float]
    after_filtering_gc_content: Optional[float]
    after_filtering_read1_mean_length: Optional[float]
    pct_adapter: Optional[float]
    bias_5_3: Optional[float]
