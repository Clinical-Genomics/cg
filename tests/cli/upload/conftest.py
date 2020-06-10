"""Fixtures for cli balsamic tests"""
import json
import logging
from pathlib import Path

import pytest

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.meta.workflow.mip_dna import AnalysisAPI
from cg.store import Store
from tests.mocks.madeline import MockMadelineAPI

LOG = logging.getLogger(__name__)


@pytest.fixture(name="scout_load_config")
def fixture_scout_load_config(apps_dir):
    """Yaml file with load information from scout"""
    return str(apps_dir / "scout/643594.config.yaml")


@pytest.fixture(scope="function", name="scout_hk_bundle_data")
def fixture_scout_hk_bundle_data(case_id, scout_load_config, timestamp):
    """Get some bundle data for housekeeper"""
    tag_name = UploadScoutAPI.get_load_config_tag()

    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [{"path": scout_load_config, "archive": False, "tags": [tag_name]}],
    }
    return hk_bundle_data


@pytest.fixture(scope="function", name="base_context")
def fixture_base_cli_context(analysis_store: Store, housekeeper_api, upload_scout_api) -> dict:
    """context to use in cli"""
    return {
        "scout_api": MockScoutApi(),
        "scout_upload_api": upload_scout_api,
        "housekeeper_api": housekeeper_api,
        "tb_api": MockTB(),
        "status": analysis_store,
    }


@pytest.fixture(scope="function", name="vogue_context")
def fixture_vogue_cli_context(vogue_api) -> dict:
    """context to use in cli"""

    return {"vogue_api": vogue_api}


@pytest.fixture(scope="function", name="upload_scout_api")
def fixture_upload_scout_api(housekeeper_api):
    """Return a upload scout api"""
    api = MockScoutUploadApi()
    api.housekeeper = housekeeper_api

    return api


@pytest.fixture(scope="function", name="vogue_api")
def fixture_vogue_api():
    """Return a MockVogueApi"""

    return MockVogueApi()


class MockTB(TrailblazerAPI):
    """Mock of trailblazer """

    def __init__(self):
        """Mock the init"""

    def get_family_root_dir(self, case_id):
        """docstring for get_family_root_dir"""
        return Path("hej")


class MockScoutApi(ScoutAPI):
    def __init__(self):
        """docstring for __init__"""
        pass

    def upload(self, scout_config, force=False):
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


class MockAnalysisApi(AnalysisAPI):
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
        self.config = {}
        self.file_exists = False
        self.lims = MockLims()

    @pytest.fixture(autouse=True)
    def _request_analysis(self, analysis_store_single_case):
        self.analysis = analysis_store_single_case

    def generate_config(self, analysis_obj, **kwargs):
        """Mock the generate config"""
        if self.mock_generate_config:
            return self.config

        return super().generate_config(analysis_obj, **kwargs)

    def save_config_file(self, scout_config, file_path):
        """docstring for save_config_file"""
        return

    def add_scout_config_to_hk(self, file_path, hk_api, case_id):
        """docstring for add_scout_config_to_hk"""
        if self.file_exists:
            raise FileExistsError("Scout config already exists")


class MockLims:
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self

    @staticmethod
    def lims_samples():
        """ Return LIMS-like family samples """
        lims_family = json.load(open("tests/fixtures/report/lims_family.json"))
        return lims_family["samples"]

    def sample(self, sample_id):
        """ Returns a lims sample matching the provided sample_id """
        for sample in self.lims_samples():
            if sample["id"] == sample_id:
                return sample
        return None
