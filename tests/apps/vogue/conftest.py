"""
    conftest for vogue API
"""

import pytest
from cg.apps.vogue import VogueAPI

CONFIG = {"vogue": {"binary_path": "/path/to/vogue", "config_path": "vogue_config"}}


@pytest.fixture(scope="function")
def vogue_config():
    """
    vogue config fixture
    """

    _config = CONFIG

    return _config


@pytest.fixture(scope="function", name="vogue_api")
def fixture_vogue_api(process):
    """
    vogue API fixture
    """

    _vogue_api = VogueAPI(CONFIG)
    _vogue_api.process = process
    return _vogue_api


@pytest.fixture(scope="function")
def genotype_dict():
    """
    genotype document fixture
    """

    return "{}"


@pytest.fixture(scope="function", name="process")
def fixture_process():
    """"""

    return MockProcess()


class MockProcess:
    def __init__(self):
        self._stderr = ""

    def run_command(self, parameters: list):
        self._stderr = " ".join(parameters)

    def stderr_lines(self):
        return self._stderr.split("\n")
