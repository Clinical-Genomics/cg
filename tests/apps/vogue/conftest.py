"""
    conftest for vogue API
"""

import pytest
from cg.apps.vogue import VogueAPI

CONFIG = {
    'vogue': {
        'binary_path': 'gtdb'
        }
    }


@pytest.fixture(scope='function')
def vogue_config():
    """
        vogue config fixture
    """

    _config = CONFIG

    return _config


@pytest.fixture(scope='function')
def vogueapi():
    """
        vogue API fixture
    """

    _vogue_api = VogueAPI(CONFIG)
    return _vogue_api


@pytest.fixture(scope='function')
def genotype_dict():
    """
        genotype document fixture
    """

    return '{}'
