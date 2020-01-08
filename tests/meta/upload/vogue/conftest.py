"""
    conftest for genotype API
"""

import pytest
from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


GTCONFIG = {
    'genotype': {
        'database': 'database',
        'config_path': '/Users/mayabrandi/opt/config/genotype.yaml',
        'binary_path': '/Users/mayabrandi/opt/cg/genotype_path'
        }
    }
VOGUECONFIG = {
    'vogue': {
        'binary_path': '/Users/mayabrandi/opt/cg/vogue_path'
        }
    }

GENOTYPE_RETURN_SAMPLE = (b'{"ACC5346A3": {"status":"pass"}, "SIB903A19": {"status":"pass"}}')

GENOTYPE_RETURN_SAMPLE_ANALYSIS = (b'{"ACC5346A3": {"snp": {}}, "SIB903A19": {"snp": {}}}')


@pytest.fixture(scope='function')
def genotype_return_sample():
    """
        genotype config fixture
    """

    _config = GENOTYPE_RETURN_SAMPLE

    return _config


@pytest.fixture(scope='function')
def genotype_return_sample_analysis():
    """
        genotype config fixture
    """

    _config = GENOTYPE_RETURN_SAMPLE_ANALYSIS

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
