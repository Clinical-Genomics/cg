from cg.models.qc_metrics import QCMetrics


class TaxprofilerQCMetrics(QCMetrics):
    """Taxprofiler QC metrics."""

    after_filtering_gc_content: float
    after_filtering_read1_mean_length: float
    after_filtering_read2_mean_length: float
    after_filtering_total_reads: float
    average_length: float
    pct_duplication: float
    raw_total_sequences: float
    reads_mapped: float
