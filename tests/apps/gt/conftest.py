"""
    conftest for genotype API
"""

import pytest
from cg.apps.gt import GenotypeAPI

CONFIG = {
    "genotype": {
        "database": "database",
        "config_path": "config/path",
        "binary_path": "gtdb",
    }
}


@pytest.fixture(scope="function")
def genotype_config():
    """
    genotype config fixture
    """

    _config = CONFIG

    return _config


@pytest.fixture(scope="function")
def genotypeapi():
    """
    genotype API fixture
    """

    _genotype_api = GenotypeAPI(CONFIG)
    return _genotype_api
