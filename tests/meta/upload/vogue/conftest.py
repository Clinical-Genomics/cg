"""
    conftest for genotype API
"""

import pytest
from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


GTCONFIG = {
    'genotype': {
        'database': 'database',
        'binary_path': 'gtdb'
        }
    }
VOGUECONFIG = {
    'vogue': {
        'binary_path': 'gtdb'
        }
    }

GENOTYPE_RETURN = (b'{"ACC5346A3": {"_id": "ACC5346A3"}, "SIB903A19": {"_id": "SIB903A19"},'
                   b'"SIB903A20": {"_id": "SIB903A20"}, "SIB903A22": {"_id": "SIB903A22"}}')


APPTAGS = [{"tag": "RMLP10R825", "category": "wgs"},
           {"tag": "METLIFR010", "category": "wes"},
           {"tag": "EXLKTTR080", "category": None}]


class MockApplication():
    """Mock Application"""

    def __init__(self, tag, category):
        self.tag = tag
        self.category = category


class MockApplicaitons():
    """
      Has function to return list of applications
    """
    def __init__(self):
        self.apptag_list = APPTAGS
        self.apptags = []

    def all(self):
        """Returning list of MockApplication instances"""
        for apptag_dict in self.apptag_list:
            apptag = MockApplication(apptag_dict['tag'], apptag_dict['category'])
            self.apptags.append(apptag)
        return self.apptags


class MockFindBasicDataHandler():
    """
        Mock for FindBasicDataHandler
    """
    def __init__(self):
        self.apptags = MockApplicaitons()

    def applications(self):
        """Returning MockApplicaitons instance"""
        return self.apptags

@pytest.fixture(scope='function')
def genotype_return_value():
    """
        genotype config fixture
    """

    _config = GENOTYPE_RETURN

    return _config


@pytest.fixture(scope='function')
def genotypeapi():
    """
        genotype API fixture
    """

    _genotype_api = GenotypeAPI(GTCONFIG)
    return _genotype_api


@pytest.fixture(scope='function')
def vogueapi():
    """
        vogue API fixture
    """

    _vogue_api = VogueAPI(VOGUECONFIG)
    return _vogue_api


@pytest.fixture(scope='function')
def find_basic():
    """
       returning FindBasicDataHandler instance
    """

    _find_basic = MockFindBasicDataHandler()
    return _find_basic
