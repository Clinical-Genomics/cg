"""
    conftest for mutacc-auto api
"""

import pytest
from cg.apps.mutacc_auto import MutaccAutoAPI

CONFIG = {
    "mutacc_auto": {
        "config_path": "mutacc-auto_config",
        "binary_path": "mutacc-auto",
        "padding": 111,
    }
}


@pytest.fixture(scope="function")
def mutacc_config():
    """
    mutacc config fixture
    """

    _config = CONFIG
    return _config


@pytest.fixture(scope="function")
def mutacc_auto_api():
    """
    mutacc-auto api
    """

    _api = MutaccAutoAPI(CONFIG)

    return _api


class MockFailedProcess:
    """
    Mock a failed process from subprocess.run()
    """

    @property
    def returncode(self):
        """ Mock returncode that is not 0"""
        return 1


@pytest.fixture(scope="function")
def mock_failed_process():
    """Return a completed process from subprocess.run()"""
    return MockFailedProcess()
