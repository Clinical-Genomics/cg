"""Delivery report mock classes and methods."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, Dict

from housekeeper.store.models import Version

from cg.apps.coverage import ChanjoAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class MockMipDNAAnalysisAPI(MipDNAAnalysisAPI):
    """Mock MipDNAAnalysisAPI for CLI tests."""

    def __init__(self, config: CGConfig):
        super().__init__(config)

    @property
    def root(self):
        return "/root/path"


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

    def create_delivery_report(
        self, case_id: str, analysis_date: datetime, force_report: bool
    ) -> None:
        """Mocked create_delivery_report method."""
        LOG.info(
            f"create_delivery_report called with the following args: case={case_id}, analysis_date={analysis_date}, "
            f"force_report={force_report}",
        )

    def create_delivery_report_file(
        self, case_id: str, directory: Path, analysis_date: datetime, force_report: bool
    ) -> Path:
        """Return mocked delivery report file path."""
        LOG.info(
            f"create_delivery_report_file called with the following args: case={case_id}, directory={directory}, "
            f"analysis_date={analysis_date}, force_report={force_report}"
        )
        return directory


class MockChanjo(ChanjoAPI):
    """Chanjo mocked class."""

    def __init__(self):
        mock_config = {"chanjo": {"config_path": "/mock/path", "binary_path": "/mock/path"}}
        super().__init__(mock_config)

    def sample_coverage(self, sample_id: str, panel_genes: list) -> Optional[Dict[str, float]]:
        """Return mocked sample dictionary."""
        sample_coverage = None
        if sample_id == "ADM1":
            sample_coverage = {"mean_coverage": 38.342, "mean_completeness": 99.1}
        elif sample_id == "ADM2":
            sample_coverage = {"mean_coverage": 37.342, "mean_completeness": 97.1}
        elif sample_id == "ADM3":
            sample_coverage = {"mean_coverage": 39.342, "mean_completeness": 98.1}
        return sample_coverage
