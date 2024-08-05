from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cg.constants import Workflow
from cg.constants.constants import FileFormat
from cg.constants.report import NA_FIELD, REPORT_QC_FLAG
from cg.io.controller import ReadFile
from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.report.rnafusion import RnafusionReportAPI
from cg.meta.report.tomte import TomteReportAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store
from tests.apps.scout.conftest import MockScoutApi
from tests.mocks.balsamic_analysis_mock import MockBalsamicAnalysis
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.report import (
    MockChanjo,
    MockHousekeeperMipDNAReportAPI,
    MockMipDNAAnalysisAPI,
)


@pytest.fixture(scope="function")
def report_api_mip_dna(
    cg_context: CGConfig, lims_samples: list[dict], report_store: Store
) -> MipDNAReportAPI:
    """MIP DNA ReportAPI fixture."""
    cg_context.meta_apis["analysis_api"] = MockMipDNAAnalysisAPI(config=cg_context)
    cg_context.status_db_ = report_store
    cg_context.lims_api_ = MockLimsAPI(cg_context, lims_samples)
    cg_context.chanjo_api_ = MockChanjo()
    cg_context.scout_api_ = MockScoutApi(cg_context)
    return MockHousekeeperMipDNAReportAPI(cg_context, cg_context.meta_apis["analysis_api"])


@pytest.fixture(scope="function")
def report_api_balsamic(
    cg_context: CGConfig, lims_samples: list[dict], report_store: Store
) -> BalsamicReportAPI:
    """BALSAMIC ReportAPI fixture."""
    cg_context.meta_apis["analysis_api"] = MockBalsamicAnalysis(cg_context)
    cg_context.status_db_ = report_store
    cg_context.lims_api_ = MockLimsAPI(cg_context, lims_samples)
    cg_context.scout_api_ = MockScoutApi(cg_context)
    return BalsamicReportAPI(cg_context, cg_context.meta_apis["analysis_api"])


@pytest.fixture(scope="function")
def report_api_rnafusion(
    rnafusion_context: CGConfig, lims_samples: list[dict]
) -> RnafusionReportAPI:
    """Rnafusion report API fixture."""
    rnafusion_context.lims_api_ = MockLimsAPI(config=rnafusion_context, samples=lims_samples)
    rnafusion_context.scout_api_ = MockScoutApi(rnafusion_context)
    return RnafusionReportAPI(
        config=rnafusion_context, analysis_api=rnafusion_context.meta_apis["analysis_api"]
    )


@pytest.fixture(scope="function")
def report_api_tomte(tomte_context: CGConfig, lims_samples: list[dict]) -> TomteReportAPI:
    """Tomte report API fixture."""
    tomte_context.lims_api_ = MockLimsAPI(config=tomte_context, samples=lims_samples)
    tomte_context.scout_api_ = MockScoutApi(tomte_context)
    return TomteReportAPI(
        config=tomte_context, analysis_api=tomte_context.meta_apis["analysis_api"]
    )


@pytest.fixture(scope="function")
def case_mip_dna(case_id: str, report_api_mip_dna: MipDNAReportAPI) -> Case:
    """MIP DNA case instance."""
    return report_api_mip_dna.status_db.get_case_by_internal_id(internal_id=case_id)


@pytest.fixture(scope="function")
def case_balsamic(case_id: str, report_api_balsamic: BalsamicReportAPI) -> Case:
    """BALSAMIC case instance."""
    return report_api_balsamic.status_db.get_case_by_internal_id(internal_id=case_id)


@pytest.fixture(scope="function")
def case_samples_data(case_id: str, report_api_mip_dna: MipDNAReportAPI):
    """MIP DNA family sample object."""
    return report_api_mip_dna.status_db.get_case_samples_by_case_id(case_internal_id=case_id)


@pytest.fixture(scope="function")
def mip_dna_analysis_api(cg_context: CGConfig) -> MockMipDNAAnalysisAPI:
    """MIP DNA analysis mock data."""
    return MockMipDNAAnalysisAPI(config=cg_context)


@pytest.fixture(scope="session")
def lims_family(fixtures_dir: Path) -> dict:
    """Returns a lims-like case of samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(fixtures_dir, "report", "lims_family.json")
    )


@pytest.fixture(scope="session")
def lims_samples(lims_family: dict) -> list[dict]:
    """Returns the samples of a lims case."""
    return lims_family["samples"]


@pytest.fixture(scope="function", autouse=True)
def report_store(analysis_store, helpers, timestamp_yesterday):
    """A mock store instance for report testing."""
    case = analysis_store.get_cases()[0]
    helpers.add_analysis(
        analysis_store, case, started_at=timestamp_yesterday, workflow=Workflow.MIP_DNA
    )
    helpers.add_analysis(analysis_store, case, started_at=datetime.now(), workflow=Workflow.MIP_DNA)
    # Mock sample dates to calculate processing times
    for family_sample in analysis_store.get_case_samples_by_case_id(
        case_internal_id=case.internal_id
    ):
        family_sample.sample.ordered_at = timestamp_yesterday - timedelta(days=2)
        family_sample.sample.received_at = timestamp_yesterday - timedelta(days=1)
        family_sample.sample.prepared_at = timestamp_yesterday
        family_sample.sample.last_sequenced_at = timestamp_yesterday
        family_sample.sample.delivered_at = datetime.now()
    return analysis_store


@pytest.fixture(scope="session")
def rnafusion_validated_metrics() -> dict[str, str]:
    """Return Rnafusion raw analysis metrics dictionary."""
    return {
        "bias_5_3": "1.12",
        "duplicates": "14.86",
        "dv200": "75.0",
        "gc_content": "51.7",
        "initial_qc": REPORT_QC_FLAG.get(True),
        "input_amount": "300.0",
        "insert_size": NA_FIELD,
        "insert_size_peak": NA_FIELD,
        "mapped_reads": "96.53",
        "mean_length_r1": "99.0",
        "million_read_pairs": "75.0",
        "mrna_bases": "85.97",
        "pct_adapter": "12.01",
        "pct_surviving": "99.42",
        "q20_rate": "97.48",
        "q30_rate": "92.95",
        "ribosomal_bases": "65.81",
        "rin": "10.0",
        "uniquely_mapped_reads": "91.02",
    }


@pytest.fixture(scope="session")
def tomte_validated_metrics() -> dict[str, str]:
    """Return Tomte analysis validated metrics dictionary."""
    return {
        "bias_5_3": "0.86",
        "duplicates": "28.94",
        "dv200": "75.0",
        "gc_content": "55.37",
        "initial_qc": REPORT_QC_FLAG.get(True),
        "input_amount": "300.0",
        "mean_length_r1": "134.0",
        "million_read_pairs": "85.0",
        "mrna_bases": "88.17",
        "pct_adapter": "50.86",
        "pct_intergenic_bases": "19.19",
        "pct_intronic_bases": "12.09",
        "pct_surviving": "99.26",
        "q20_rate": "96.69",
        "q30_rate": "90.95",
        "ribosomal_bases": "55.11",
        "rin": "10.0",
        "uniquely_mapped_reads": "67.28",
    }
