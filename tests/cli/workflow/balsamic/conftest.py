"""Fixtures for cli balsamic tests"""

import pytest
from cg.apps.balsamic.fastq import FastqHandler
from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.workflow.balsamic import AnalysisAPI
from cg.store import Store, models

from tests.store_helpers import ensure_bed_version, ensure_customer, add_sample, add_family


@pytest.fixture
def balsamic_context(balsamic_store) -> dict:
    """context to use in cli"""
    return {
        "hk_api": MockHouseKeeper(),
        "db": balsamic_store,
        "analysis_api": MockAnalysis,
        "fastq_handler": MockFastq,
        "gzipper": MockGzip(),
        "lims_api": MockLims(),
        "bed_path": "bed_path",
        "balsamic": {
            "conda_env": "conda_env",
            "root": "root",
            "slurm": {"account": "account", "qos": "qos"},
            "singularity": "singularity",
            "reference_config": "reference_config",
        },
    }


class MockHouseKeeper(HousekeeperAPI):
    """Mock HousekeeperAPI"""

    def __init__(self):
        pass

    def get_files(self, bundle: str, tags: list, version: int = None):
        """Mock get_files of HousekeeperAPI"""
        del tags, bundle, version
        return [MockFile()]


class MockLims(LimsAPI):
    """Mock LimsAPI"""

    lims = None

    def __init__(self):
        self.lims = self
        pass

    def capture_kit(self, lims_id: str) -> str:
        return "dummy_capture_kit"


@pytest.fixture(scope="function")
def lims_api():
    """Mock lims_api"""

    _lims_api = MockLims()
    return _lims_api


class MockFile:
    """Mock File"""

    def __init__(self, path=""):
        self.path = path
        self.full_path = path


class MockGzip:
    """Mock gzip"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self

    def open(self, full_path):
        """Mock the gzip open function"""
        del full_path
        return self

    def readline(self):
        """Mock the gzip readline function"""
        return MockLine()


class MockLine:
    """Mock line from readline"""

    def decode(self):
        """Mock the gzip.readline.decode function"""
        return "headerline"


class MockAnalysis(AnalysisAPI):
    """Mock AnalysisAPI"""

    @staticmethod
    def fastq_header(line):
        """Mock AnalysisAPI.fastq_header"""
        del line

        _header = {"lane": "1", "flowcell": "ABC123", "readnumber": "1"}

        return _header


class MockFastq(FastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        pass


@pytest.fixture(scope="function")
def balsamic_store(base_store: Store, lims_api) -> Store:
    """real store to be used in tests"""
    _store = base_store

    case = add_family(_store, "balsamic_case")
    tumour_sample = add_sample(_store, "tumour_sample", is_tumour=True, application_type="tgs")
    normal_sample = add_sample(_store, "normal_sample", is_tumour=False, application_type="tgs")
    _store.relate_sample(case, tumour_sample, status="unknown")
    _store.relate_sample(case, normal_sample, status="unknown")

    case = add_family(_store, "mip_case")
    normal_sample = add_sample(_store, "normal_sample", is_tumour=False, data_analysis="mip")
    _store.relate_sample(case, normal_sample, status="unknown")

    bed_name = lims_api.capture_kit(tumour_sample.internal_id)
    ensure_bed_version(_store, bed_name)

    case_wgs = add_family(_store, "balsamic_case_wgs")
    tumour_sample_wgs = add_sample(
        _store,
        "tumour_sample_wgs",
        is_tumour=True,
        application_tag="dummy_tag_wgs",
        application_type="wgs",
    )
    normal_sample_wgs = add_sample(
        _store,
        "normal_sample_wgs",
        is_tumour=False,
        application_tag="dummy_tag_wgs",
        application_type="wgs",
    )
    _store.relate_sample(case_wgs, tumour_sample_wgs, status="unknown")
    _store.relate_sample(case_wgs, normal_sample_wgs, status="unknown")

    _store.commit()

    return _store


@pytest.fixture(scope="function")
def balsamic_case(analysis_store) -> models.Family:
    """case with balsamic data_type"""
    return analysis_store.find_family(ensure_customer(analysis_store), "balsamic_case")


@pytest.fixture(scope="function")
def balsamic_case_wgs(analysis_store) -> models.Family:
    """case with balsamic data_type"""
    return analysis_store.find_family(ensure_customer(analysis_store), "balsamic_case_wgs")


@pytest.fixture(scope="function")
def mip_case(analysis_store) -> models.Family:
    """case with balsamic data_type"""
    return analysis_store.find_family(ensure_customer(analysis_store), "mip_case")
