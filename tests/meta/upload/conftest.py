"""Fixtures for meta/upload tests"""
import pytest

from cg.apps.coverage.api import ChanjoAPI
from cg.apps.hk import HousekeeperAPI
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.mutacc import UploadToMutaccAPI
from cg.meta.upload.observations import UploadObservationsAPI
from cg.meta.upload.scoutapi import UploadScoutAPI


class MockVersion:
    """Mock a version object"""

    # In this case we need to disable since this needsto be mocked
    @property
    def id(self):
        """Mock out the id"""
        return ""

    @property
    def app_root(self):
        """Mock out the app_root"""
        return None


class MockFile:
    """Mock the housekeeper File class"""

    def __init__(self, path="", to_archive=False, tags=None):
        self.path = path
        self.to_archive = to_archive
        self.tags = tags or []

    def first(self):
        """Mock the first method"""
        return MockFile(path=self.path)

    @property
    def full_path(self):
        """Mock the full path attribute"""
        return self.path

    @staticmethod
    def is_included():
        """Mock the is_included method to always return False"""
        return False


class MockHouseKeeper(HousekeeperAPI):
    """Mock the housekeeper API"""

    # In this mock we want to override __init__ so disable here
    def __init__(self):
        self._file_added = False
        self._file_included = False
        self._files = []
        self._file = MockFile()

    # This is overriding a housekeeper object so ok to not include all arguments
    def files(self, version, tags):
        """Mock the files method to return a list of files"""
        return self._file

    def get_files(self, bundle, tags, version="1.0"):
        """Mock the get_files method to return a list of files"""
        return self._files

    def add_file(self, file, version_obj, tags, to_archive=False):
        """Mock the add_files method to add a MockFile to the list of files"""
        self._file_added = True
        self._file = MockFile(path=file)
        return self._file

    def version(self, bundle: str, date: str):
        """Fetch version from the database."""
        return MockVersion()

    def last_version(self, bundle: str):
        """docstring for last_version"""
        return MockVersion()

    def include_file(self, file_obj, version_obj):
        """docstring for include_file"""
        self._file_included = True

    def add_commit(self, file_obj):
        """Overrides sqlalchemy method"""
        return file_obj


class MockAnalysis:
    """Mock an analysis object"""

    @staticmethod
    def get_latest_metadata(family_id=None):
        """Mock get_latest_metadata"""
        # Returns: dict: parsed data
        # Define output dict
        outdata = {
            "analysis_sex": {"ADM1": "female", "ADM2": "female", "ADM3": "female"},
            "family": family_id or "yellowhog",
            "duplicates": {"ADM1": 13.525, "ADM2": 12.525, "ADM3": 14.525},
            "genome_build": "hg19",
            "rank_model_version": "1.18",
            "mapped_reads": {"ADM1": 98.8, "ADM2": 99.8, "ADM3": 97.8},
            "mip_version": "v4.0.20",
            "sample_ids": ["2018-20203", "2018-20204"],
            "sv_rank_model_version": "1.08",
        }

        return outdata

    @staticmethod
    def convert_panels(customer_id, panels):
        """Mock convert_panels"""
        return ""


class MockCoverage(ChanjoAPI):
    """Mock chanjo coverage api"""

    pass


class MockMutaccAuto:
    """ Mock class for mutacc_auto api """

    @staticmethod
    def extract_reads(*args, **kwargs):
        """mock extract_reads method"""
        _, _ = args, kwargs

    @staticmethod
    def import_reads(*args, **kwargs):
        """ mock import_reads method """
        _, _ = args, kwargs


class MockScoutApi:
    """Mock class for Scout api"""

    @staticmethod
    def get_causative_variants(case_id):
        """mock get_causative_variants"""
        _ = case_id
        return []

    @property
    def client(self):
        """Client URI"""
        return "mongodb://"

    @property
    def name(self):
        """Name property"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @name.deleter
    def name(self):
        del self._name


class MockLoqusAPI:
    """ Mock LoqusAPI class"""

    def __init__(self, analysis_type="wgs"):
        self.analysis_type = analysis_type

    @staticmethod
    def load(*args, **kwargs):
        """ Mock load method"""
        _ = args
        _ = kwargs
        return dict(variants=12)

    @staticmethod
    def get_case(*args, **kwargs):
        """ Mock get_case method"""
        _ = args
        _ = kwargs
        return {"case_id": "case_id", "_id": "123"}

    @staticmethod
    def get_duplicate(*args, **kwargs):
        """Mock get_duplicate method"""
        _ = args
        _ = kwargs
        return {"case_id": "case_id"}


@pytest.yield_fixture(scope="function")
def housekeeper_api():
    """housekeeper_api fixture"""
    _api = MockHouseKeeper()

    yield _api


@pytest.yield_fixture(scope="function")
def upload_observations_api(analysis_store):
    """ Create mocked UploadObservationsAPI object"""

    loqus_mock = MockLoqusAPI()
    hk_mock = MockHouseKeeper()
    hk_mock.add_file(file=".", version_obj="", tags=[])

    _api = UploadObservationsAPI(
        status_api=analysis_store, hk_api=hk_mock, loqus_api=loqus_mock
    )

    yield _api


@pytest.yield_fixture(scope="function")
def upload_observations_api_wes(analysis_store):
    """ Create mocked UploadObservationsAPI object"""

    loqus_mock = MockLoqusAPI(analysis_type="wes")
    hk_mock = MockHouseKeeper()
    hk_mock.add_file(file=".", version_obj="", tags=[])

    _api = UploadObservationsAPI(
        status_api=analysis_store, hk_api=hk_mock, loqus_api=loqus_mock
    )

    yield _api


@pytest.yield_fixture(scope="function")
def upload_scout_api(scout_store, madeline_api):
    """Fixture for upload_scout_api"""
    hk_mock = MockHouseKeeper()
    hk_mock.add_file(file="/mock/path", version_obj="", tags=[])
    analysis_mock = MockAnalysis()

    _api = UploadScoutAPI(
        hk_api=hk_mock,
        scout_api=scout_store,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
    )

    yield _api


@pytest.yield_fixture(scope="function")
def mutacc_upload_api():
    """
        Fixture for a mutacc upload api
    """

    scout_api = MockScoutApi()
    mutacc_auto_api = MockMutaccAuto()

    _api = UploadToMutaccAPI(scout_api=scout_api, mutacc_auto_api=mutacc_auto_api)

    return _api


@pytest.yield_fixture(scope="function")
def coverage_upload_api(chanjo_config_dict):
    """Fixture for coverage upload API"""
    hk_api = MockHouseKeeper()
    hk_api.add_file(file="path", version_obj="", tags=[])
    status_api = None
    coverage_api = MockCoverage(chanjo_config_dict)
    _api = UploadCoverageApi(
        status_api=status_api, hk_api=hk_api, chanjo_api=coverage_api
    )
    return _api


@pytest.yield_fixture(scope="function")
def analysis(analysis_store):
    """Fixture to mock an analysis"""
    _analysis = analysis_store.add_analysis(pipeline="pipeline", version="version")
    _analysis.family = analysis_store.family("yellowhog")
    _analysis.config_path = "dummy_path"
    yield _analysis
