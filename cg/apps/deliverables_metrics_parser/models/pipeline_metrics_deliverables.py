"""Module for the pipeline metrics deliverables models."""
from pydantic import BaseModel, Field


class MIPDNAMetricsDeliverables(BaseModel):
    sample_id: str = None
    gender: str = None
    pct_pf_reads_improper_pairs: list[str] = Field(..., alias="PCT_PF_READS_IMPROPER_PAIRS")
    mean_target_coverage: str = Field(..., alias="MEAN_TARGET_COVERAGE")
    at_dropout: str = Field(..., alias="AT_DROPOUT")
    raw_total_sequences: list[int] = None
    fraction_duplicates: float = None
    median_target_coverage: int = Field(..., alias="MEDIAN_TARGET_COVERAGE")
    percentage_mapped_reads: list[int] = None
    pct_target_bases_10x: float = Field(..., alias="PCT_TARGET_BASES_10X")
    reads_mapped: list[int] = None
    gc_dropout: float = Field(..., alias="GC_DROPOUT")
    mean_insert_size: float = Field(..., alias="MEAN_INSERT_SIZE")
    pct_off_bait: float = Field(..., alias="PCT_OFF_BAIT")
    pct_target_bases_20x: float = Field(..., alias="PCT_TARGET_BASES_20X")
    fold_80_base_penalty: float = Field(..., alias="FOLD_80_BASE_PENALTY")
