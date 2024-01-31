from cg.meta.workflow.pre_analysis_quality_check.models import PreAnalysisQualityMetrics


class PreAnalysisQualityCheck:
    def __init__(self, pre_analysis_quality_metrics: PreAnalysisQualityMetrics) -> None:
        """
        Initialize the PreAnalysisQualityCheck class.

        Args:
            case (Case): The case object.

        """
        self.pre_analysis_quality_metrics: PreAnalysisQualityMetrics = pre_analysis_quality_metrics

    def run_qc(self) -> bool:
        """
        Run the qc for the case.

        Returns:
            bool: True if the case passes the qc, False otherwise.

        """
        return self.pre_analysis_quality_metrics.sequencing_metrics.sequencing_quality
