
"""
    conftest for mutacc-auto api
"""

import pytest

from cg.apps.mutacc_auto import MutaccAutoAPI

CONFIG = {
    'mutacc-auto': {
        'config_path': 'mutacc-auto_config',
        'binary_path': 'mutacc-auto',
        'padding': 111
        }
    }


@pytest.fixture(scope='function')
def mutacc_config():
    """
        mutacc config fixture
    """

    _config = CONFIG
    return _config


@pytest.fixture(scope='function')
def mutacc_auto_api():
    """
        mutacc-auto api
    """

    _api = MutaccAutoAPI(CONFIG)

    return _api


class MockCompletedProcess:
    """
        Mock a completed process from subprocess.run()
    """
    @property
    def returncode(self):
        """ Mock returncode """
        # Mock a != 0 returncode
        return 1


@pytest.fixture(scope='function')
def mock_completed_process():
    """Return a completed process from subprocess.run()"""
    return MockCompletedProcess()
