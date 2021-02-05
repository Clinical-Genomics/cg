"""Fixtures for cli balsamic tests"""
import json
import logging
from datetime import datetime
from pathlib import Path

import pytest
from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.meta.upload.scout.scout_load_config import ScoutLoadConfig
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import Store, models
from tests.meta.upload.scout.conftest import fixture_mip_load_config
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.mocks.madeline import MockMadelineAPI

LOG = logging.getLogger(__name__)


@pytest.fixture(name="scout_load_config")
def fixture_scout_load_config(apps_dir) -> Path:
    """Yaml file with load information from scout"""
    return apps_dir / "scout/643594.config.yaml"


@pytest.fixture(scope="function", name="scout_hk_bundle_data")
def fixture_scout_hk_bundle_data(case_id: str, scout_load_config: Path, timestamp: datetime):
    """Get some bundle data for housekeeper"""
    tag_name = UploadScoutAPI.get_load_config_tag()

    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [{"path": str(scout_load_config), "archive": False, "tags": [tag_name]}],
    }
    return hk_bundle_data


@pytest.fixture(name="upload_genotypes_hk_bundle")
def fixture_upload_genotypes_hk_bundle(
    case_id: str, timestamp, case_qc_metrics: Path, bcf_file: Path
) -> dict:
    """ Returns a dictionary in hk format with files used in upload gt process"""
    data = {
        "name": case_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {"path": str(case_qc_metrics), "archive": False, "tags": ["qcmetrics"]},
            {"path": str(bcf_file), "archive": False, "tags": ["snv-gbcf"]},
        ],
    }
    return data


@pytest.fixture(name="analysis_obj")
def fixture_analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers
) -> models.Analysis:
    """Return a analysis object with a trio"""
    return analysis_store_trio.family(case_id).analyses[0]


@pytest.fixture(name="upload_genotypes_hk_api")
def fixture_upload_genotypes_hk_api(
    real_housekeeper_api: HousekeeperAPI,
    upload_genotypes_hk_bundle: dict,
    analysis_obj: models.Analysis,
    helpers,
) -> HousekeeperAPI:
    """Add and include files from upload genotypes hk bundle"""
    helpers.ensure_hk_bundle(real_housekeeper_api, upload_genotypes_hk_bundle)
    hk_version = real_housekeeper_api.last_version(analysis_obj.family.internal_id)
    real_housekeeper_api.include(hk_version)
    return real_housekeeper_api


@pytest.fixture(name="upload_genotypes_context")
def fixture_upload_genotypes_context(
    upload_genotypes_hk_api: HousekeeperAPI, genotype_api: GenotypeAPI, analysis_store_trio: Store
) -> dict:
    """Create a upload genotypes context"""

    return {
        "genotype_api": genotype_api,
        "housekeeper_api": upload_genotypes_hk_api,
        "status_db": analysis_store_trio,
    }


@pytest.fixture(name="scout_load_object")
def fixture_scout_load_object(case_id: str, timestamp: datetime) -> ScoutLoadConfig:
    """Create a scout load config case object"""
    case_data = {
        "owner": "cust000",
        "case": case_id,
        "human_genome_build": "37",
        "rank_score_threshold": 5,
        "analysis_date": timestamp,
        "samples": [
            {"sample_id": "sample", "sex": "male", "phenotype": "affected", "analysis_type": "wgs"}
        ],
    }
    return ScoutLoadConfig(**case_data)


@pytest.fixture(scope="function", name="base_context")
def fixture_base_cli_context(
    analysis_store: Store, housekeeper_api, upload_scout_api, trailblazer_api
) -> dict:
    """context to use in cli"""
    return {
        "scout_api": MockScoutApi(),
        "scout_upload_api": upload_scout_api,
        "housekeeper_api": housekeeper_api,
        "trailblazer_api": trailblazer_api,
        "status_db": analysis_store,
        "mip-rd-dna": {"root": "hej"},
    }


@pytest.fixture(scope="function", name="vogue_context")
def fixture_vogue_cli_context(vogue_api) -> dict:
    """context to use in cli"""

    return {"vogue_api": vogue_api}


@pytest.fixture(scope="function", name="upload_scout_api")
def fixture_upload_scout_api(housekeeper_api: MockHousekeeperAPI, mip_load_config: ScoutLoadConfig):
    """Return a upload scout api"""
    api = MockScoutUploadApi()
    api.housekeeper = housekeeper_api
    api.config = mip_load_config

    return api


@pytest.fixture(scope="function", name="vogue_api")
def fixture_vogue_api():
    """Return a MockVogueApi"""

    return MockVogueApi()


class MockScoutApi(ScoutAPI):
    def __init__(self):
        """docstring for __init__"""
        pass

    def upload(self, scout_load_config: Path, threshold: int = 5, force: bool = False):
        """docstring for upload"""
        LOG.info("Case loaded successfully to Scout")


class MockVogueApi:
    def __init__(self):
        """docstring for __init__"""
        pass

    def load_reagent_labels(self, days: int):
        """docstring for upload"""

    def load_samples(self, days: int):
        """docstring for upload"""

    def load_flowcells(self, days: int):
        """docstring for upload"""


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
    def lims_samples():
        """ Return LIMS-like case samples """
        lims_family = json.load(open("tests/fixtures/report/lims_family.json"))
        return lims_family["samples"]

    def sample(self, sample_id):
        """ Returns a lims sample matching the provided sample_id """
        for sample in self.lims_samples():
            if sample["id"] == sample_id:
                return sample
        return None
