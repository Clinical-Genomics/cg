"""Delivery report mock classes and methods."""

import logging
from datetime import datetime
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.coverage import ChanjoAPI
from cg.constants.constants import AnalysisType, GenomeVersion
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Case
from tests.mocks.mip_analysis_mock import create_mip_metrics_deliverables

LOG = logging.getLogger(__name__)


class MockMipDNAAnalysisAPI(MipDNAAnalysisAPI):
    """Mock MipDNAAnalysisAPI for CLI tests."""

    def __init__(self, config: CGConfig):
        super().__init__(config)

    @property
    def root(self):
        return "/root/path"

    @staticmethod
    def get_latest_metadata(family_id: str = None, **kwargs) -> MipAnalysis:
        metrics: MIPMetricsDeliverables = create_mip_metrics_deliverables()
        return MipAnalysis(
            case=family_id or "yellowhog",
            genome_build=GenomeVersion.hg19.value,
            sample_id_metrics=metrics.sample_id_metrics,
            mip_version="v4.0.20",
            rank_model_version="1.18",
            sample_ids=["2018-20203", "2018-20204"],
            sv_rank_model_version="1.08",
        )

    def get_data_analysis_type(self, case: Case) -> str | None:
        """Return data analysis type carried out."""
        return AnalysisType.WHOLE_GENOME_SEQUENCING


class MockHousekeeperMipDNAReportAPI(MipDNAReportAPI):
    """Mock ReportAPI for CLI tests overwriting Housekeeper methods."""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config, analysis_api)

    def add_delivery_report_to_hk(
        self, case_id: str, delivery_report_file: Path, version: Version
    ) -> None:
        """Mocked add_delivery_report_to_hk method."""
        LOG.info(
            f"add_delivery_report_to_hk called with the following args:  case={case_id}, delivery_report_file="
            f"{delivery_report_file}, version={version}"
        )

    def get_delivery_report_from_hk(self, case_id: str, version: Version) -> None:
        """Return mocked delivery report path stored in Housekeeper."""
        LOG.info(
            f"get_delivery_report_from_hk called with the following args: case={case_id}, version={version}"
        )
        return None

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> str:
        """Return mocked uploaded to Scout file."""
        LOG.info(
            f"get_scout_uploaded_file_from_hk called with the following args: case={case_id}, scout_tag={scout_tag}"
        )
        return f"path/to/{scout_tag}"


class MockMipDNAReportAPI(MockHousekeeperMipDNAReportAPI):
    """Mock ReportAPI for CLI tests."""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config, analysis_api)

    def create_delivery_report(self, case_id: str, analysis_date: datetime, force: bool) -> None:
        """Mocked create_delivery_report method."""
        LOG.info(
            f"create_delivery_report called with the following args: case={case_id}, analysis_date={analysis_date}, "
            f"force={force}",
        )

    def create_delivery_report_file(
        self, case_id: str, directory: Path, analysis_date: datetime, force: bool
    ) -> Path:
        """Return mocked delivery report file path."""
        LOG.info(
            f"create_delivery_report_file called with the following args: case={case_id}, directory={directory}, "
            f"analysis_date={analysis_date}, force={force}"
        )
        return directory


class MockChanjo(ChanjoAPI):
    """Chanjo mocked class."""

    def __init__(self):
        mock_config = {"chanjo": {"config_path": "/mock/path", "binary_path": "/mock/path"}}
        super().__init__(mock_config)

    def sample_coverage(self, sample_id: str, panel_genes: list) -> dict[str, float] | None:
        """Return mocked sample dictionary."""
        sample_coverage = None
        if sample_id == "ADM1":
            sample_coverage = {"mean_coverage": 38.342, "mean_completeness": 99.1}
        elif sample_id == "ADM2":
            sample_coverage = {"mean_coverage": 37.342, "mean_completeness": 97.1}
        elif sample_id == "ADM3":
            sample_coverage = {"mean_coverage": 39.342, "mean_completeness": 98.1}
        return sample_coverage
