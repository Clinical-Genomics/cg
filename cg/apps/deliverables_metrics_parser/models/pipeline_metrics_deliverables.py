"""Module for the pipeline metrics deliverables models."""
from pydantic import BaseModel


class MIPDNAMetricsDeliverables(BaseModel):
    sample_id: str = None
    gender: str = None
    PCT_PF_READS_IMPROPER_PAIRS: list[str] = None
    MEAN_TARGET_COVERAGE: str = None
    AT_DROPOUT: str = None
    raw_total_sequences: list[int] = None
    fraction_duplicates: float = None
    MEDIAN_TARGET_COVERAGE: int = None
    percentage_mapped_reads: list[int] = None
    PCT_TARGET_BASES_10X: float = None
    reads_mapped: list[int] = None
    GC_DROPOUT: float = None
    MEAN_INSERT_SIZE: float = None
    PCT_OFF_BAIT: float = None
    PCT_TARGET_BASES_20X: float = None
    FOLD_80_BASE_PENALTY: float = None
