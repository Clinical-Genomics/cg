from pydantic import BaseModel


class RarediseaseQCMetrics(BaseModel):
    """Raredisease QC metrics"""

    #  bamstats:
    percentage_mapped_reads: float | None
    #  collecthsmetrics:
    PCT_TARGET_BASES_10X: float | None
    MEDIAN_TARGET_COVERAGE: float | None
    #  collectmultiplemetrics:
    PCT_PF_READS_ALIGNED: float | None
    PCT_PF_READS_IMPROPER_PAIRS: float | None
    PCT_ADAPTER: float | None
    #  markduplicates:
    fraction_duplicates: float | None
