"""
    conftest for genotype API
"""

import pytest
from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


GTCONFIG = {
    'genotype': {
        'database': 'database',
        'binary_path': '/Users/mayabrandi/opt/cg/genotype_path'
        }
    }
VOGUECONFIG = {
    'vogue': {
        'binary_path': '/Users/mayabrandi/opt/cg/vogue_path'
        }
    }

GENOTYPE_RETURN = (b'{"ACC5346A3": {"_id": "ACC5346A3"}, "SIB903A19": {"_id": "SIB903A19"},'
                   b'"SIB903A20": {"_id": "SIB903A20"}, "SIB903A22": {"_id": "SIB903A22"}}')


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
