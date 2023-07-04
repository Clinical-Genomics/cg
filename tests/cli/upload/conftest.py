"""Fixtures for cli balsamic tests."""

from typing import Union

import logging
from datetime import datetime
from pathlib import Path
from tempfile import tempdir

import pytest
from cgmodels.cg.constants import Pipeline
from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.constants import FileFormat
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.constants.housekeeper_tags import HkMipAnalysisTag, GensAnalysisTag, HK_DELIVERY_REPORT_TAG
from cg.io.controller import ReadFile
from cg.meta.deliver import DeliverAPI
from cg.meta.rsync import RsyncAPI
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.scout.scout_load_config import ScoutLoadConfig
from cg.store import Store
from cg.store.models import Analysis
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.report import MockMipDNAReportAPI
from tests.store_helpers import StoreHelpers

from tests.meta.upload.scout.conftest import fixture_mip_load_config
from tests.cli.workflow.mip.conftest import (
    fixture_mip_rna_context,
    fixture_mip_dna_context,
    fixture_mip_case_ids,
    fixture_mip_case_id,
)

LOG = logging.getLogger(__name__)


@pytest.fixture(name="upload_genotypes_hk_bundle")
def fixture_upload_genotypes_hk_bundle(
    case_id: str, timestamp, case_qc_metrics_deliverables: Path, bcf_file: Path
) -> dict:
    """Returns a dictionary in hk format with files used in upload gt process"""
    return {
        "name": case_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {
                "path": str(case_qc_metrics_deliverables),
                "archive": False,
                "tags": HkMipAnalysisTag.QC_METRICS,
            },
            {"path": str(bcf_file), "archive": False, "tags": ["snv-gbcf", "genotype"]},
        ],
    }


@pytest.fixture(name="analysis_obj")
def fixture_analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers
) -> Analysis:
    """Return a analysis object with a trio"""
    return analysis_store_trio.get_case_by_internal_id(internal_id=case_id).analyses[0]


@pytest.fixture(name="upload_genotypes_hk_api")
def fixture_upload_genotypes_hk_api(
    real_housekeeper_api: HousekeeperAPI,
    upload_genotypes_hk_bundle: dict,
    analysis_obj: Analysis,
    helpers,
) -> HousekeeperAPI:
    """Add and include files from upload genotypes hk bundle"""
    helpers.ensure_hk_bundle(real_housekeeper_api, upload_genotypes_hk_bundle)
    hk_version = real_housekeeper_api.last_version(analysis_obj.family.internal_id)
    real_housekeeper_api.include(hk_version)
    return real_housekeeper_api


@pytest.fixture(name="upload_gens_hk_bundle")
def fixture_upload_gens_hk_bundle(
    case_id: str,
    gens_coverage_path: Path,
    gens_fracsnp_path: Path,
    later_timestamp: datetime,
    sample_id: str,
    timestamp: datetime,
) -> dict:
    """Returns a dictionary in Housekeeper format with files used in upload gens process."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": later_timestamp,
        "files": [
            {
                "path": gens_coverage_path.as_posix(),
                "archive": False,
                "tags": [sample_id] + GensAnalysisTag.COVERAGE,
            },
            {
                "path": gens_fracsnp_path.as_posix(),
                "archive": False,
                "tags": [sample_id] + GensAnalysisTag.FRACSNP,
            },
        ],
    }


@pytest.fixture(name="upload_gens_hk_api")
def fixture_upload_gens_hk_api(
    case_id: str,
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    upload_gens_hk_bundle: dict,
) -> HousekeeperAPI:
    """Add and include files from upload_gens_hk_bundle."""
    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=upload_gens_hk_bundle)
    hk_version = real_housekeeper_api.last_version(bundle=case_id)
    real_housekeeper_api.include(hk_version)
    return real_housekeeper_api


@pytest.fixture(name="upload_gens_context")
def fixture_upload_gens_context(
    analysis_store_trio: Store,
    base_context: CGConfig,
    gens_api: GensAPI,
    upload_gens_hk_api: HousekeeperAPI,
) -> CGConfig:
    """Create a gens upload context."""
    base_context.gens_api_ = gens_api
    base_context.housekeeper_api_ = upload_gens_hk_api
    base_context.status_db_ = analysis_store_trio
    return base_context


@pytest.fixture(name="upload_report_hk_bundle")
def fixture_upload_report_hk_bundle(case_id: str, delivery_report_html: Path, timestamp) -> dict:
    """Returns a dictionary including the delivery report html file"""

    return {
        "name": case_id,
        "created": datetime.now(),
        "files": [
            {"path": str(delivery_report_html), "archive": False, "tags": [HK_DELIVERY_REPORT_TAG]}
        ],
    }


@pytest.fixture(name="upload_report_hk_api")
def fixture_upload_report_hk_api(
    real_housekeeper_api: HousekeeperAPI,
    upload_report_hk_bundle: dict,
    analysis_obj: Analysis,
    helpers,
) -> HousekeeperAPI:
    """Add and include files from upload reports hk bundle"""

    helpers.ensure_hk_bundle(real_housekeeper_api, upload_report_hk_bundle)
    hk_version = real_housekeeper_api.last_version(analysis_obj.family.internal_id)
    real_housekeeper_api.include(hk_version)
    return real_housekeeper_api


@pytest.fixture(name="base_context")
def fixture_base_context(
    analysis_store: Store,
    housekeeper_api: HousekeeperAPI,
    upload_scout_api: UploadScoutAPI,
    trailblazer_api: TrailblazerAPI,
    cg_context: CGConfig,
) -> CGConfig:
    """context to use in cli"""
    cg_context.status_db_ = analysis_store
    cg_context.housekeeper_api_ = housekeeper_api
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.scout_api_ = MockScoutApi()
    cg_context.meta_apis["scout_upload_api"] = upload_scout_api
    cg_context.mip_rd_dna.root = tempdir

    return cg_context


@pytest.fixture(name="fastq_context")
def fixture_fastq_context(
    base_context,
    analysis_store: Store,
    housekeeper_api: HousekeeperAPI,
    upload_scout_api: UploadScoutAPI,
    trailblazer_api: TrailblazerAPI,
    cg_context: CGConfig,
) -> CGConfig:
    """Fastq context to use in cli"""

    base_context.meta_apis["delivery_api"] = DeliverAPI(
        store=base_context.status_db,
        hk_api=base_context.housekeeper_api,
        case_tags=PIPELINE_ANALYSIS_TAG_MAP[Pipeline.FASTQ]["case_tags"],
        sample_tags=PIPELINE_ANALYSIS_TAG_MAP[Pipeline.FASTQ]["sample_tags"],
        delivery_type="fastq",
        project_base_path=Path(base_context.delivery_path),
    )
    base_context.meta_apis["rsync_api"] = RsyncAPI(cg_context)
    base_context.trailblazer_api_ = trailblazer_api
    return base_context


@pytest.fixture(scope="function", name="upload_scout_api")
def fixture_upload_scout_api(housekeeper_api: MockHousekeeperAPI, mip_load_config: ScoutLoadConfig):
    """Return a upload scout api"""
    api = MockScoutUploadApi()
    api.housekeeper = housekeeper_api
    api.config = mip_load_config

    return api


class MockScoutApi(ScoutAPI):
    def __init__(self):
        """docstring for __init__"""

    def upload(self, scout_load_config: Path, force: bool = False):
        """docstring for upload"""
        LOG.info("Case loaded successfully to Scout")


class MockAnalysisApi(MipAnalysisAPI):
    def __init__(self):
        """docstring for __init__"""

    def get_latest_metadata(self, internal_id):
        """docstring for upload"""
        return {}


class MockScoutUploadApi(UploadScoutAPI):
    def __init__(self, **kwargs):
        """docstring for __init__"""
        self.mock_generate_config = True
        self.housekeeper = None
        self.madeline_api = MockMadelineAPI()
        self.analysis = MockAnalysisApi()
        self.config = ScoutLoadConfig()
        self.file_exists = False
        self.lims = MockLims()
        self.missing_mandatory_field = False

    @pytest.fixture(autouse=True)
    def _request_analysis(self, analysis_store_single_case):
        self.analysis = analysis_store_single_case

    def generate_config(self, analysis_obj, **kwargs):
        """Mock the generate config"""
        if self.missing_mandatory_field:
            self.config.vcf_snv = None

        return self.config

    def save_config_file(self, upload_config, file_path):
        """docstring for save_config_file"""
        return

    def add_scout_config_to_hk(self, config_file_path: str, case_id: str, delete: bool = False):
        """docstring for add_scout_config_to_hk"""
        LOG.info("Use mock to upload file")
        if self.file_exists:
            raise FileExistsError("Scout config already exists")


class MockLims:
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self

    @staticmethod
    def lims_samples() -> dict:
        """Return LIMS-like case samples"""
        lims_case: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.JSON,
            file_path=Path("tests", "fixtures", "report", "lims_family.json"),
        )
        return lims_case["samples"]

    def sample(self, sample_id) -> Union[str, None]:
        """Returns a lims sample matching the provided sample_id"""
        for sample in self.lims_samples():
            if sample["id"] == sample_id:
                return sample
        return None


@pytest.fixture(name="upload_context")
def upload_context(cg_context: CGConfig) -> CGConfig:
    analysis_api = MipDNAAnalysisAPI(config=cg_context)
    cg_context.meta_apis["analysis_api"] = analysis_api
    cg_context.meta_apis["report_api"] = MockMipDNAReportAPI(cg_context, analysis_api)
    cg_context.meta_apis["scout_upload_api"] = UploadScoutAPI(
        hk_api=cg_context.housekeeper_api,
        scout_api=cg_context.scout_api,
        madeline_api=cg_context.madeline_api,
        analysis_api=analysis_api,
        lims_api=cg_context.lims_api,
        status_db=cg_context.status_db,
    )

    return cg_context
