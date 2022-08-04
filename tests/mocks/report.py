import logging
from datetime import datetime
from pathlib import Path
from typing import Union, Optional

from cg.apps.coverage import ChanjoAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store

LOG = logging.getLogger(__name__)


class MockMipDNAAnalysisAPI(MipDNAAnalysisAPI):
    """Mock MipDNAAnalysisAPI for CLI tests"""

    def __init__(self, config: CGConfig):
        super().__init__(config)

    @property
    def root(self):
        """docstring for root"""

        return "/root/path"


class MockHousekeeperMipDNAReportAPI(MipDNAReportAPI):
    """Mock ReportAPI for CLI tests overwriting HK methods"""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config, analysis_api)

    def add_delivery_report_to_hk(
        self, delivery_report_file: Path, case_id: str, analysis_date: datetime
    ):
        """docstring for add_delivery_report_to_hk"""

        LOG.info(
            "add_delivery_report_to_hk called with the following args: delivery_report_file=%s, case=%s, "
            "analysis_date=%s",
            delivery_report_file,
            case_id,
            analysis_date,
        )

    def get_delivery_report_from_hk(self, case_id: str) -> str:
        """docstring for get_delivery_report_from_hk"""

        LOG.info(f"get_delivery_report_from_hk called with the following args: case={case_id}")

        return "/path/to/delivery_report.html"

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> Optional[str]:
        """docstring for get_scout_uploaded_file_from_hk"""

        LOG.info(
            "add_delivery_report_to_hk called with the following args: case=%s, scout_tag=%s",
            case_id,
            scout_tag,
        )

        return f"path/to/{scout_tag}"


class MockMipDNAReportAPI(MockHousekeeperMipDNAReportAPI):
    """Mock ReportAPI for CLI tests"""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config, analysis_api)

    def create_delivery_report(self, case_id: str, analysis_date: datetime, force_report: bool):
        """docstring for create_delivery_report"""

        LOG.info(
            "create_delivery_report called with the following args: case=%s, analysis_date=%s, force_report=%s",
            case_id,
            analysis_date,
            force_report,
        )

    def create_delivery_report_file(
        self, case_id: str, file_path: Path, analysis_date: datetime, force_report: bool
    ):
        """docstring for create_delivery_report_file"""

        LOG.info(
            "create_delivery_report_file called with the following args: case=%s, file_path=%s, analysis_date=%s, "
            "force_report=%s",
            case_id,
            file_path,
            analysis_date,
            force_report,
        )

        return file_path


class MockDB(Store):
    """Mock database"""

    def __init__(self, store):
        self.store = store


class MockChanjo(ChanjoAPI):
    """Chanjo mock class"""

    def __init__(self):
        mock_config = {"chanjo": {"config_path": "/mock/path", "binary_path": "/mock/path"}}
        super().__init__(mock_config)

    def sample_coverage(self, sample_id: str, panel_genes: list) -> Union[None, dict]:
        """Calculates sample coverage for a specific panel"""

        sample_coverage = None
        if sample_id == "ADM1":
            sample_coverage = {"mean_coverage": 38.342, "mean_completeness": 99.1}
        elif sample_id == "ADM2":
            sample_coverage = {"mean_coverage": 37.342, "mean_completeness": 97.1}
        elif sample_id == "ADM3":
            sample_coverage = {"mean_coverage": 39.342, "mean_completeness": 98.1}

        return sample_coverage
