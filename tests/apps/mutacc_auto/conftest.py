"""
conftest for mutacc-auto api
"""

import pytest


class MockFailedProcess:
    """
    Mock a failed process from subprocess.run()
    """

    @property
    def returncode(self):
        """Mock returncode that is not 0"""
        return 1


@pytest.fixture(scope="function")
def mock_failed_process():
    """Return a completed process from subprocess.run()"""
    return MockFailedProcess()
