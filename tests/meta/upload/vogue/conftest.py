"""
    conftest for genotype API
"""

import pytest
from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


GTCONFIG = {
    "genotype": {
        "database": "database",
        "config_path": "/Users/mayabrandi/opt/config/genotype.yaml",
        "binary_path": "/Users/mayabrandi/opt/cg/genotype_path",
    }
}
VOGUECONFIG = {"vogue": {"binary_path": "/Users/mayabrandi/opt/cg/vogue_path"}}

GENOTYPE_RETURN_SAMPLE = (
    b'{"ACC5346A3": {"status":"pass"}, "SIB903A19": {"status":"pass"}}'
)

GENOTYPE_RETURN_SAMPLE_ANALYSIS = (
    b'{"ACC5346A3": {"snp": {}}, "SIB903A19": {"snp": {}}}'
)


@pytest.fixture(scope="function")
def genotype_return_sample():
    """
        genotype config fixture
    """

    _config = GENOTYPE_RETURN_SAMPLE

    return _config


APPTAGS = [
    {"tag": "RMLP10R825", "category": "wgs"},
    {"tag": "METLIFR010", "category": "wes"},
    {"tag": "EXLKTTR080", "category": None},
]


class MockApplication:
    """Mock Application"""

    def __init__(self, tag, category):
        self.tag = tag
        self.category = category


class MockApplicaitons:
    """
      Has function to return list of applications
    """

    def __init__(self):
        self.apptag_list = APPTAGS
        self.apptags = []

    def all(self):
        """Returning list of MockApplication instances"""
        for apptag_dict in self.apptag_list:
            apptag = MockApplication(apptag_dict["tag"], apptag_dict["category"])
            self.apptags.append(apptag)
        return self.apptags


class MockFindBasicDataHandler:
    """
        Mock for FindBasicDataHandler
    """

    def __init__(self):
        self.apptags = MockApplicaitons()

    def applications(self):
        """Returning MockApplicaitons instance"""
        return self.apptags


@pytest.fixture(scope="function")
def genotype_return_sample_analysis():
    """
        genotype config fixture
    """

    _config = GENOTYPE_RETURN_SAMPLE_ANALYSIS

    return _config


@pytest.fixture(scope="function")
def genotypeapi():
    """
        genotype API fixture
    """

    _genotype_api = GenotypeAPI(GTCONFIG)
    return _genotype_api


@pytest.fixture(scope="function")
def vogueapi():
    """
        vogue API fixture
    """

    _vogue_api = VogueAPI(VOGUECONFIG)
    return _vogue_api


@pytest.fixture(scope="function")
def find_basic():
    """
       returning FindBasicDataHandler instance
    """

    _find_basic = MockFindBasicDataHandler()
    return _find_basic
