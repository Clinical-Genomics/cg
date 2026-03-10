from cg.constants.constants import SexOptions
from cg.models.qc_metrics import QCMetrics


class RarediseaseQCMetrics(QCMetrics):
    """Raredisease QC metrics."""

    # TODO: 2. Replace mapped_reads and total_reads for the percentage of aligned reads
    mapped_reads: int
    percent_duplication: float
    predicted_sex_sex_check: SexOptions
    total_reads: int
