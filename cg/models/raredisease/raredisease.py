from cg.constants.constants import SexOptions
from cg.models.qc_metrics import QCMetrics


class RarediseaseQCMetrics(QCMetrics):
    """Raredisease QC metrics."""

    mapped_reads: int
    percent_duplication: float
    predicted_sex_sex_check: SexOptions
    total_reads: int
