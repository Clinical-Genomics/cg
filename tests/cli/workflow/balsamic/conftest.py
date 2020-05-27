"""Fixtures for cli balsamic tests"""

from pathlib import Path

import pytest

from cg.apps.balsamic.fastq import FastqHandler
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.meta.workflow.balsamic import AnalysisAPI
from cg.store import Store, models


@pytest.fixture
def balsamic_context(
    balsamic_store, balsamic_case, housekeeper_api, hk_bundle_data, helpers
) -> dict:
    """context to use in cli"""
    hk_bundle_data["name"] = balsamic_case.internal_id
    helpers.ensure_hk_bundle(housekeeper_api, hk_bundle_data)

    return {
        "hk_api": housekeeper_api,
        "tb_api": MockTB(),
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


@pytest.fixture(scope="function", name="balsamic_store")
def fixture_balsamic_store(base_store: Store, lims_api, helpers) -> Store:
    """real store to be used in tests"""
    _store = base_store

    case = helpers.add_family(_store, "balsamic_case")
    tumour_sample = helpers.add_sample(
        _store, "tumour_sample", is_tumour=True, application_type="tgs"
    )
    normal_sample = helpers.add_sample(
        _store, "normal_sample", is_tumour=False, application_type="tgs"
    )
    helpers.add_relationship(_store, family=case, sample=tumour_sample)
    helpers.add_relationship(_store, family=case, sample=normal_sample)

    case = helpers.add_family(_store, "mip_case")
    normal_sample = helpers.add_sample(
        _store, "normal_sample", is_tumour=False, data_analysis="mip"
    )
    helpers.add_relationship(_store, family=case, sample=normal_sample)

    bed_name = lims_api.capture_kit(tumour_sample.internal_id)
    helpers.ensure_bed_version(_store, bed_name)

    case_wgs = helpers.add_family(_store, "balsamic_case_wgs")
    tumour_sample_wgs = helpers.add_sample(
        _store,
        "tumour_sample_wgs",
        is_tumour=True,
        application_tag="dummy_tag_wgs",
        application_type="wgs",
    )
    normal_sample_wgs = helpers.add_sample(
        _store,
        "normal_sample_wgs",
        is_tumour=False,
        application_tag="dummy_tag_wgs",
        application_type="wgs",
    )
    helpers.add_relationship(_store, family=case_wgs, sample=tumour_sample_wgs)
    helpers.add_relationship(_store, family=case_wgs, sample=normal_sample_wgs)

    return _store


class MockTB(TrailblazerAPI):
    """Mock of trailblazer """

    def __init__(self):
        """Override TrailblazerAPI __init__ to avoid default behaviour"""

    def analyses(self, *args, **kwargs):
        """Override TrailblazerAPI analyses method to avoid default behaviour"""
        return []


@pytest.fixture(name="balsamic_dir")
def fixture_balsamic_dir(apps_dir: Path) -> Path:
    """Return the path to the balsamic apps dir"""
    return apps_dir / "balsamic"


@pytest.fixture(name="balsamic_case_dir")
def fixture_balsamic_case_dir(balsamic_dir: Path) -> Path:
    """Return the path to the balsamic apps case dir"""
    return balsamic_dir / "case"


@pytest.fixture(scope="function")
def deliverables_file(balsamic_case_dir):
    """Return a balsamic deliverables file"""
    return str(balsamic_case_dir / "metadata.yml")


@pytest.fixture(scope="function")
def deliverables_file_directory(balsamic_case_dir):
    """Return a balsamic deliverables file that specifies a directory"""
    return str(balsamic_case_dir / "metadata_directory.yml")


@pytest.fixture(scope="function")
def deliverables_file_tags(balsamic_case_dir):
    """Return a balsamic deliverables file containing one file with two tags"""
    return str(balsamic_case_dir / "metadata_file_tags.yml")


@pytest.fixture(scope="function", name="balsamic_case")
def fixture_balsamic_case(balsamic_store, helpers) -> models.Family:
    """Case with balsamic data_type"""
    return balsamic_store.find_family(
        helpers.ensure_customer(balsamic_store), "balsamic_case"
    )


@pytest.fixture(scope="function", name="balsamic_case_wgs")
def fixture_balsamic_case_wgs(balsamic_store, helpers) -> models.Family:
    """Case with balsamic data_type"""
    return balsamic_store.find_family(
        helpers.ensure_customer(balsamic_store), "balsamic_case_wgs"
    )


@pytest.fixture(scope="function", name="mip_case")
def fixture_mip_case(balsamic_store, helpers) -> models.Family:
    """Case with balsamic data_type"""
    return balsamic_store.find_family(
        helpers.ensure_customer(balsamic_store), "mip_case"
    )
