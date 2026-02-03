from cg.models.qc_metrics import QCMetrics


class TomteQCMetrics(QCMetrics):
    """Tomte QC metrics."""

    after_filtering_gc_content: float
    after_filtering_q20_rate: float
    after_filtering_q30_rate: float
    after_filtering_read1_mean_length: float
    before_filtering_total_reads: float
    median_5prime_to_3prime_bias: float
    pct_adapter: float
    pct_duplication: float
    pct_intergenic_bases: float
    pct_intronic_bases: float
    pct_mrna_bases: float
    pct_ribosomal_bases: float
    pct_surviving: float
    uniquely_mapped_percent: float
