import pytest

from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.meta.upload.observations import UploadObservationsAPI


class MockVersion:
    def id(self):
        return ''


class MockFile:

    def __init__(self, path=''):
        self.path = path

    def first(self):
        return MockFile()

    def full_path(self):
        return ''


# Mock File again, but full_path should be an attribute
class MockFile1():

    """ Mock File object """

    def __init__(self, path=''):
        self.full_path = path

    @staticmethod
    def first():
        """ mock first method """
        return MockFile1()


class MockHouseKeeper:

    def files(self, version, tags):
        return MockFile()

    def version(self, arg1: str, arg2: str):
        """Fetch version from the database."""
        return MockVersion()


# Mock Housekeeper again, but with MockFile_ returned from files instead
class MockHouseKeeper1():

    """ Mock housekeeper api"""

    @staticmethod
    def files(version, tags):
        """ Mock files method """
        _, _ = version, tags
        return MockFile1()

    @staticmethod
    def version(arg1: str, arg2: str):
        """Fetch version from the database."""
        _, _ = arg1, arg2
        return MockVersion()


class MockMadeline:

    def make_ped(self, name, samples):
        return ''

    def run(self, arg1: str, arg2: str):
        """Fetch version from the database."""
        return MockVersion()


class MockAnalysis:

    def get_latest_metadata(self, family_id):
        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            'analysis_sex': {'ADM1': 'female', 'ADM2': 'female', 'ADM3': 'female'},
            'family': 'yellowhog',
            'duplicates': {'ADM1': 13.525, 'ADM2': 12.525, 'ADM3': 14.525},
            'genome_build': 'hg19',
            'rank_model_version': '1.18',
            'mapped_reads': {'ADM1': 98.8, 'ADM2': 99.8, 'ADM3': 97.8},
            'mip_version': 'v4.0.20',
            'sample_ids': ['2018-20203', '2018-20204'],
        }

        return outdata

    def convert_panels(self, customer_id, panels):
        return ''


class MockLoqusAPI:

    """ Mock LoqusAPI class"""

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
        return {'case_id': 'case_id', '_id': '123'}

    @staticmethod
    def get_duplicate(*args, **kwargs):
        """Mock get_duplicate method"""
        _ = args
        _ = kwargs
        return {'case_id': 'case_id'}


@pytest.yield_fixture(scope='function')
def upload_observations_api(analysis_store):

    """ Create mocked UploadObservationsAPI object"""

    loqus_mock = MockLoqusAPI()
    hk_mock = MockHouseKeeper1()

    _api = UploadObservationsAPI(
        status_api=analysis_store,
        hk_api=hk_mock,
        loqus_api=loqus_mock
    )

    yield _api

@pytest.yield_fixture(scope='function')
def upload_scout_api(analysis_store, scout_store):

    madeline_mock = MockMadeline()
    hk_mock = MockHouseKeeper()
    analysis_mock = MockAnalysis()

    _api = UploadScoutAPI(
        status_api=analysis_store,
        hk_api=hk_mock,
        scout_api=scout_store,
        madeline_exe='',
        madeline=madeline_mock,
        analysis_api=analysis_mock
    )

    yield _api


@pytest.yield_fixture(scope='function')
def analysis(analysis_store):
    _analysis = analysis_store.add_analysis(pipeline='pipeline', version='version')
    _analysis.family = analysis_store.family('yellowhog')
    _analysis.config_path = 'dummy_path'
    yield _analysis
