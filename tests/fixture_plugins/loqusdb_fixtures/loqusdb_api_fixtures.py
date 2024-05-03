"""Loqusdb API fixtures."""

import pytest

from cg.apps.loqus import LoqusdbAPI
from cg.models.cg_config import CGConfig
from tests.mocks.process_mock import ProcessMock


@pytest.fixture
def loqusdb_id() -> str:
    """Returns a Loqusdb mock ID."""
    return "01ab23cd"


@pytest.fixture
def loqusdb_binary_path(cg_context: CGConfig) -> str:
    """Return Loqusdb binary path."""
    return cg_context.loqusdb.binary_path


@pytest.fixture
def loqusdb_config_path(cg_context: CGConfig) -> str:
    """Return Loqusdb config dictionary."""
    return cg_context.loqusdb.config_path


@pytest.fixture
def loqusdb_process(loqusdb_binary_path: str, loqusdb_config_path: str) -> ProcessMock:
    """Return mocked process instance."""
    return ProcessMock(binary=loqusdb_binary_path, config=loqusdb_config_path)


@pytest.fixture
def loqusdb_process_exception(loqusdb_binary_path: str, loqusdb_config_path: str) -> ProcessMock:
    """Return error process instance."""
    return ProcessMock(binary=loqusdb_binary_path, config=loqusdb_config_path, error=True)


@pytest.fixture
def loqusdb_api(
    loqusdb_binary_path: str, loqusdb_config_path: str, loqusdb_process: ProcessMock
) -> LoqusdbAPI:
    """Return Loqusdb API."""
    loqusdb_api = LoqusdbAPI(binary_path=loqusdb_binary_path, config_path=loqusdb_config_path)
    loqusdb_api.process = loqusdb_process
    return loqusdb_api


@pytest.fixture
def loqusdb_api_exception(
    loqusdb_binary_path: str, loqusdb_config_path: str, loqusdb_process_exception: ProcessMock
) -> LoqusdbAPI:
    """Return Loqusdb API with mocked error process."""
    loqusdb_api = LoqusdbAPI(binary_path=loqusdb_binary_path, config_path=loqusdb_config_path)
    loqusdb_api.process = loqusdb_process_exception
    return loqusdb_api
