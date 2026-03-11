from cg.constants.constants import SexOptions
from cg.models.qc_metrics import QCMetrics


class RarediseaseQCMetrics(QCMetrics):
    """Raredisease QC metrics."""

    percent_duplication: float
    picard_pct_pf_reads_aligned: float
    predicted_sex_sex_check: SexOptions
