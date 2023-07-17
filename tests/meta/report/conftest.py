from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pytest

from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.report.rnafusion import RnafusionReportAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family
from tests.apps.scout.conftest import MockScoutApi
from tests.mocks.balsamic_analysis_mock import MockBalsamicAnalysis
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.mip_analysis_mock import MockMipAnalysis
from tests.mocks.report import MockChanjo, MockHousekeeperMipDNAReportAPI


@pytest.fixture(scope="function", name="report_api_mip_dna")
def report_api_mip_dna(
    cg_context: CGConfig, lims_samples: List[dict], report_store: Store
) -> MipDNAReportAPI:
    """MIP DNA ReportAPI fixture."""
    cg_context.meta_apis["analysis_api"] = MockMipAnalysis()
    cg_context.status_db_ = report_store
    cg_context.lims_api_ = MockLimsAPI(cg_context, lims_samples)
    cg_context.chanjo_api_ = MockChanjo()
    cg_context.scout_api_ = MockScoutApi(cg_context)
    return MockHousekeeperMipDNAReportAPI(cg_context, cg_context.meta_apis["analysis_api"])


@pytest.fixture(scope="function", name="report_api_balsamic")
def report_api_balsamic(
    cg_context: CGConfig, lims_samples: List[dict], report_store: Store
) -> BalsamicReportAPI:
    """BALSAMIC ReportAPI fixture."""
    cg_context.meta_apis["analysis_api"] = MockBalsamicAnalysis(cg_context)
    cg_context.status_db_ = report_store
    cg_context.lims_api_ = MockLimsAPI(cg_context, lims_samples)
    cg_context.scout_api_ = MockScoutApi(cg_context)
    return BalsamicReportAPI(cg_context, cg_context.meta_apis["analysis_api"])


@pytest.fixture(scope="function", name="report_api_rnafusion")
def report_api_rnafusion(
    rnafusion_context: CGConfig, lims_samples: List[dict]
) -> RnafusionReportAPI:
    """Rnafusion report API fixture."""
    rnafusion_context.lims_api_ = MockLimsAPI(rnafusion_context, lims_samples)
    rnafusion_context.scout_api_ = MockScoutApi(rnafusion_context)
    return RnafusionReportAPI(rnafusion_context, rnafusion_context.meta_apis["analysis_api"])


@pytest.fixture(scope="function", name="case_mip_dna")
def case_mip_dna(case_id: str, report_api_mip_dna: MipDNAReportAPI) -> Family:
    """MIP DNA case instance."""
    return report_api_mip_dna.status_db.get_case_by_internal_id(internal_id=case_id)


@pytest.fixture(scope="function", name="case_balsamic")
def case_balsamic(case_id: str, report_api_balsamic: BalsamicReportAPI) -> Family:
    """BALSAMIC case instance."""
    return report_api_balsamic.status_db.get_case_by_internal_id(internal_id=case_id)


@pytest.fixture(scope="function", name="case_samples_data")
def case_samples_data(case_id: str, report_api_mip_dna: MipDNAReportAPI):
    """MIP DNA family sample object."""
    return report_api_mip_dna.status_db.get_case_samples_by_case_id(case_internal_id=case_id)


@pytest.fixture(scope="function", name="mip_analysis_api")
def mip_analysis_api() -> MockMipAnalysis:
    """MIP analysis mock data."""
    return MockMipAnalysis()


@pytest.fixture(scope="session", name="lims_family")
def fixture_lims_family(fixtures_dir: Path) -> dict:
    """Returns a lims-like case of samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(fixtures_dir, "report", "lims_family.json")
    )


@pytest.fixture(scope="session", name="lims_samples")
def fixture_lims_samples(lims_family: dict) -> List[dict]:
    """Returns the samples of a lims case."""
    return lims_family["samples"]


@pytest.fixture(scope="function", autouse=True, name="report_store")
def report_store(analysis_store, helpers, timestamp_yesterday):
    """A mock store instance for report testing."""
    case = analysis_store.get_cases()[0]
    helpers.add_analysis(
        analysis_store, case, pipeline=Pipeline.MIP_DNA, started_at=timestamp_yesterday
    )
    helpers.add_analysis(analysis_store, case, pipeline=Pipeline.MIP_DNA, started_at=datetime.now())
    # Mock sample dates to calculate processing times
    for family_sample in analysis_store.get_case_samples_by_case_id(
        case_internal_id=case.internal_id
    ):
        family_sample.sample.ordered_at = timestamp_yesterday - timedelta(days=2)
        family_sample.sample.received_at = timestamp_yesterday - timedelta(days=1)
        family_sample.sample.prepared_at = timestamp_yesterday
        family_sample.sample.sequenced_at = timestamp_yesterday
        family_sample.sample.delivered_at = datetime.now()
    return analysis_store


@pytest.fixture(scope="session", name="rnafusion_validated_metrics")
def fixture_rnafusion_validated_metrics() -> Dict[str, str]:
    """Return Rnafusion raw analysis metrics dictionary."""
    return {
        "gc_content": "51.7",
        "ribosomal_bases": "65.81",
        "q20_rate": "97.48",
        "q30_rate": "92.95",
        "mapped_reads": "96.53",
        "rin": "10.0",
        "input_amount": "300.0",
        "insert_size": "N/A",
        "insert_size_peak": "N/A",
        "mean_length_r1": "99.0",
        "million_read_pairs": "75.0",
        "bias_5_3": "1.07",
        "pct_adapter": "12.01",
        "duplicates": "14.86",
        "mrna_bases": "85.97",
        "pct_surviving": "99.42",
        "uniquely_mapped_reads": "91.02",
    }
