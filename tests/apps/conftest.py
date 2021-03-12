"""Fixtures for testing apps"""

from pathlib import Path

import pytest
import requests

from cg.utils.commands import Process

# File fixtures for the apps


@pytest.fixture
def balsamic_orderform(orderforms: Path) -> str:
    """Orderform fixture for Balsamic samples"""
    _file = orderforms / "1508.22.balsamic.xlsx"
    return str(_file)


@pytest.fixture
def external_orderform(orderforms: Path) -> str:
    """Orderform fixture for external samples"""
    _file = orderforms / "1541.6.external.xlsx"
    return str(_file)


@pytest.fixture
def fastq_orderform(orderforms: Path):
    """Orderform fixture for fastq samples"""
    _file = orderforms / "1508.22.fastq.xlsx"
    return str(_file)


@pytest.fixture
def metagenome_orderform(orderforms: Path) -> str:
    """Orderform fixture for metagenome samples"""
    _file = orderforms / "1605.9.metagenome.xlsx"
    return str(_file)


@pytest.fixture
def mip_orderform(orderforms: Path) -> str:
    """Orderform fixture for MIP samples"""
    _file = orderforms / "1508.22.mip.xlsx"
    return str(_file)


@pytest.fixture
def mip_rna_orderform(orderforms: Path) -> str:
    """Orderform fixture for MIP RNA samples"""
    _file = orderforms / "1508.22.mip_rna.xlsx"
    return str(_file)


@pytest.fixture
def response():
    """Mock a requests.response object"""

    class MockResponse(requests.Response):
        """Mock requests.response class"""

        def __init__(self):
            pass

        @property
        def ok(self):
            """Mock ok"""
            return False

        @property
        def text(self):
            """Mock text"""
            return "response text"

        @property
        def reason(self):
            """Mock reason"""
            return "response reason"

    return MockResponse()


@pytest.fixture
def mock_process():
    """Fixture returns mock Process class factory"""

    def _mock_process(result_stderr: str, result_stdout: str):
        class MockProcess(Process):
            """Process class with mocked run_command method"""

            def run_command(self, parameters=None):
                """Overrides originial run_command method"""
                self.stdout = result_stdout
                self.stderr = result_stderr

        return MockProcess

    return _mock_process
