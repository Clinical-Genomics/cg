"""Module for the pipeline metrics deliverables models."""
from pydantic import BaseModel


class MIPDNAMetricsDeliverables(BaseModel):
    sample_id: str
    gender: str
    PCT_PF_READS_IMPROPER_PAIRS: list[str]
    MEAN_TARGET_COVERAGE: str
    AT_DROPOUT: str
    raw_total_sequences: list[int]
    fraction_duplicates: float
    MEDIAN_TARGET_COVERAGE: int
    percentage_mapped_reads: list[int]
    PCT_TARGET_BASES_10X: float
    reads_mapped: list[int]
    GC_DROPOUT: float
    MEAN_INSERT_SIZE: float
    PCT_OFF_BAIT: float
    PCT_TARGET_BASES_20X: float
    FOLD_80_BASE_PENALTY: float
