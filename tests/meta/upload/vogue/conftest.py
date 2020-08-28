"""
    conftest for genotype API
"""

import pytest
from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


GTCONFIG = {
    "genotype": {
        "database": "database",
        "config_path": "/path/to/config/genotype.yaml",
        "binary_path": "/path/to/genotype_path",
    }
}
VOGUECONFIG = {"vogue": {"binary_path": "/path/to/vogue_path", "config_path": "vogue_config"}}

GENOTYPE_RETURN_SAMPLE = b'{"ACC5346A3": {"status":"pass"}, "SIB903A19": {"status":"pass"}}'

GENOTYPE_RETURN_SAMPLE_ANALYSIS = b'{"ACC5346A3": {"snp": {}}, "SIB903A19": {"snp": {}}}'


@pytest.fixture(scope="function")
def genotype_return():
    """
    genotype config fixture
    """

    _configs = {
        "sample": GENOTYPE_RETURN_SAMPLE,
        "sample_analysis": GENOTYPE_RETURN_SAMPLE_ANALYSIS,
    }

    return _configs


APPTAGS = [
    {"tag": "RMLP10R825", "prep_category": "wgs"},
    {"tag": "METLIFR010", "prep_category": "wes"},
]


class MockApplication:
    """Mock Application"""

    def __init__(self, tag, prep_category):
        self.tag = tag
        self.prep_category = prep_category


class MockApplications:
    """
    Has function to return list of applications
    """

    def __init__(self):
        self.apptag_list = APPTAGS
        self.apptags = []

    def all(self):
        """Returning list of MockApplication instances"""
        for apptag_dict in self.apptag_list:
            apptag = MockApplication(apptag_dict["tag"], apptag_dict["prep_category"])
            self.apptags.append(apptag)
        return self.apptags


class MockStore:
    """
    Mock for Store
    """

    def __init__(self):
        self.apptags = MockApplications()

    def applications(self):
        """Returning MockApplications instance"""
        return self.apptags


@pytest.fixture(scope="function")
def genotype_api():
    """
    genotype API fixture
    """

    _genotype_api = GenotypeAPI(GTCONFIG)
    return _genotype_api


@pytest.fixture(scope="function")
def vogue_api():
    """
    vogue API fixture
    """

    _vogue_api = VogueAPI(VOGUECONFIG)
    return _vogue_api


@pytest.fixture(scope="function")
def store():
    """
    returning MockStore instance
    """

    _store = MockStore()
    return _store
