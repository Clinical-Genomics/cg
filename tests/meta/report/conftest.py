from pathlib import Path

from datetime import datetime, timedelta
from typing import List

import pytest
from cgmodels.cg.constants import Pipeline

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from tests.apps.scout.conftest import MockScoutApi
from tests.mocks.balsamic_analysis_mock import MockBalsamicAnalysis
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.mip_analysis_mock import MockMipAnalysis
from tests.mocks.report import MockChanjo, MockDB, MockHousekeeperMipDNAReportAPI


@pytest.fixture(scope="function", name="report_api_mip_dna")
def report_api_mip_dna(cg_context: CGConfig, lims_samples) -> MipDNAReportAPI:
    """MIP DNA ReportAPI fixture."""

    cg_context.meta_apis["analysis_api"] = MockMipAnalysis()
    cg_context.status_db_ = MockDB(report_store)
    cg_context.lims_api_ = MockLimsAPI(cg_context, lims_samples)
    cg_context.chanjo_api_ = MockChanjo()
    cg_context.scout_api_ = MockScoutApi(cg_context)
    return MockHousekeeperMipDNAReportAPI(cg_context, cg_context.meta_apis["analysis_api"])


@pytest.fixture(scope="function", name="report_api_balsamic")
def report_api_balsamic(cg_context: CGConfig, lims_samples) -> BalsamicReportAPI:
    """BALSAMIC ReportAPI fixture."""

    cg_context.meta_apis["analysis_api"] = MockBalsamicAnalysis(cg_context)
    cg_context.status_db_ = MockDB(report_store)
    cg_context.lims_api_ = MockLimsAPI(cg_context, lims_samples)
    cg_context.scout_api_ = MockScoutApi(cg_context)
    return BalsamicReportAPI(cg_context, cg_context.meta_apis["analysis_api"])


@pytest.fixture(scope="function", name="case_mip_dna")
def case_mip_dna(case_id, report_api_mip_dna) -> models.Family:
    """MIP DNA case instance."""

    return report_api_mip_dna.status_db.family(case_id)


@pytest.fixture(scope="function", name="case_balsamic")
def case_balsamic(case_id, report_api_balsamic) -> models.Family:
    """BALSAMIC case instance."""

    return report_api_balsamic.status_db.family(case_id)


@pytest.fixture(scope="function", name="case_samples_data")
def case_samples_data(case_id, report_api_mip_dna):
    """MIP DNA family sample object."""

    return report_api_mip_dna.status_db.family_samples(case_id)


@pytest.fixture(name="mip_analysis_api")
def mip_analysis_api() -> MockMipAnalysis:
    """MIP analysis mock data."""

    return MockMipAnalysis()


@pytest.fixture(name="lims_family")
def fixture_lims_family(fixtures_dir: Path) -> dict:
    """Returns a lims-like case of samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(fixtures_dir, "report", "lims_family.json")
    )


@pytest.fixture(name="lims_samples")
def fixture_lims_samples(lims_family: dict) -> List[dict]:
    """Returns the samples of a lims case."""

    return lims_family["samples"]


@pytest.fixture(scope="function", autouse=True, name="report_store")
def report_store(analysis_store, helpers, timestamp_yesterday):
    """A mock store instance for report testing."""

    case = analysis_store.families()[0]
    helpers.add_analysis(
        analysis_store, case, pipeline=Pipeline.MIP_DNA, started_at=timestamp_yesterday
    )
    helpers.add_analysis(analysis_store, case, pipeline=Pipeline.MIP_DNA, started_at=datetime.now())

    # Mock sample dates to calculate processing times
    for family_sample in analysis_store.family_samples(case.internal_id):
        family_sample.sample.ordered_at = timestamp_yesterday - timedelta(days=2)
        family_sample.sample.received_at = timestamp_yesterday - timedelta(days=1)
        family_sample.sample.prepared_at = timestamp_yesterday
        family_sample.sample.sequenced_at = timestamp_yesterday
        family_sample.sample.delivered_at = datetime.now()

    return analysis_store
