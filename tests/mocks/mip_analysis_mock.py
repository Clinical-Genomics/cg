from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables


def create_mip_metrics_deliverables():
    """Get an mip_metrics_deliverables object."""
    metrics_deliverables: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML,
        file_path=Path("tests", "fixtures", "apps", "mip", "case_metrics_deliverables.yaml"),
    )
    return MIPMetricsDeliverables(**metrics_deliverables)


class MockMipAnalysis(MipAnalysisAPI):
    """Mock MIP analysis object."""

    @staticmethod
    def get_latest_metadata(family_id=None):
        """Mock get_latest_metadata."""
        # Returns: dict: parsed data
        # Define output dict
        metrics: MIPMetricsDeliverables = create_mip_metrics_deliverables()
        return MipAnalysis(
            case=family_id or "yellowhog",
            genome_build="hg19",
            sample_id_metrics=metrics.sample_id_metrics,
            mip_version="v4.0.20",
            rank_model_version="1.18",
            sample_ids=["2018-20203", "2018-20204"],
            sv_rank_model_version="1.08",
        )
