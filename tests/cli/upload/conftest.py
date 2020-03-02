"""Fixtures for cli balsamic tests"""

from pathlib import Path

import pytest

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.meta.workflow.mip_dna import AnalysisAPI
from cg.store import Store


@pytest.fixture(scope="function", name="base_context")
def fixture_base_context(analysis_store_single_case: Store) -> dict:
    """context to use in cli"""

    return {
        "scout_api": MockScoutApi(),
        "scout_upload_api": MockScoutUploadApi(),
        "housekeeper_api": MockHK(),
        "tb_api": MockTB(),
        "status": analysis_store_single_case,
    }


@pytest.fixture(scope="function", name="analysis_family_single_case")
def fixture_analysis_family_single():
    """Build an example family."""
    family = {
        "name": "family",
        "internal_id": "yellowhog",
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "proband",
                "sex": "male",
                "internal_id": "ADM1",
                "status": "affected",
                "ticket_number": 123456,
                "reads": 5000000,
            }
        ],
    }
    return family


@pytest.yield_fixture(scope="function", name="analysis_store_single_case")
def fixture_analysis_store_single(base_store, analysis_family_single_case):
    """Setup a store instance for testing analysis API."""
    analysis_family = analysis_family_single_case
    customer = base_store.customer("cust000")
    family = base_store.Family(
        name=analysis_family["name"],
        panels=analysis_family["panels"],
        internal_id=analysis_family["internal_id"],
        priority="standard",
    )
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application("WGTPCFC030").versions[0]
    for sample_data in analysis_family["samples"]:
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=sample_data["sex"],
            internal_id=sample_data["internal_id"],
            ticket=sample_data["ticket_number"],
            reads=sample_data["reads"],
        )
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family["samples"]:
        sample_obj = base_store.sample(sample_data["internal_id"])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data["status"],
            father=base_store.sample(sample_data["father"])
            if sample_data.get("father")
            else None,
            mother=base_store.sample(sample_data["mother"])
            if sample_data.get("mother")
            else None,
        )
        base_store.add(link)

    _analysis = base_store.add_analysis(pipeline="pipeline", version="version")
    _analysis.family = family
    _analysis.config_path = "dummy_path"

    base_store.commit()
    yield base_store


@pytest.fixture
def hk_mock():
    """docstring for hk_mock"""
    return MockHK()


class MockTB(TrailblazerAPI):
    """Mock of trailblazer """

    def __init__(self):
        """Mock the init"""

    def get_family_root_dir(self, case_id):
        """docstring for get_family_root_dir"""
        return Path("hej")


class MockVersion:
    """Mock a version object"""

    @property
    def id(self):
        return ""


class MockFile:
    """Mock a file object"""

    def __init__(self, path="", to_archive=False, tags=None, **kwargs):
        self.path = path
        self.to_archive = to_archive
        self.tags = tags or []
        self._empty_first = kwargs.get("empty_first", False)

    def first(self):
        if self._empty_first:
            return None
        return MockFile()

    def full_path(self):
        return ""

    def is_included(self):
        return False


class MockHK(HousekeeperAPI):
    """Mock of housekeeper """

    def __init__(self):
        """Mock the init"""
        self.delivery_report = True

    def files(self, **kwargs):
        """docstring for file"""
        if (
            "delivery-report" in kwargs.get("tags", [])
            and self.delivery_report is False
        ):
            return MockFile(empty_first=True)
        return MockFile()

    def version(self, arg1: str, arg2: str):
        """Fetch version from the database."""
        return MockVersion()


class MockFamily(object):
    """Mock of family used in store """

    def __init__(self):
        """Mock the init"""
        self.analyses = ["analysis_obj"]


class MockScoutApi(ScoutAPI):
    def __init__(self):
        """docstring for __init__"""
        pass

    def upload(self, scout_config, force=False):
        """docstring for upload"""
        pass


class MockAnalysisApi(AnalysisAPI):
    def __init__(self):
        """docstring for __init__"""
        pass

    def get_latest_metadata(self, internal_id):
        """docstring for upload"""
        return {}


class MockScoutUploadApi(UploadScoutAPI):
    def __init__(self, **kwargs):
        """docstring for __init__"""
        self.mock_generate_config = True
        self.housekeeper = MockHK()
        self.analysis = MockAnalysisApi()
        self.config = {}
        self.file_exists = False

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


class MockLims(LimsAPI):
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self

    _project_name = None
    _sample_sex = None

    def update_project(self, lims_id: str, name=None):
        """Mock lims update_project"""
        self._project_name = name

    def get_updated_project_name(self) -> str:
        """Method to test that update project was called with name parameter"""
        return self._project_name

    def update_sample(
        self,
        lims_id: str,
        sex=None,
        application: str = None,
        target_reads: int = None,
        priority=None,
    ):
        """Mock lims update_sample"""
        self._sample_sex = sex

    def get_updated_sample_sex(self) -> str:
        """Method to be used to test that update_sample was called with sex parameter"""
        return self._sample_sex
