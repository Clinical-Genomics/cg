"""Fixtures for observations."""

import pytest

from cg.apps.loqus import LoqusdbAPI


class MockLoqusdbAPI(LoqusdbAPI):
    """Mock LoqusdbAPI class."""

    def __init__(self, binary_path: str, config_path: str):
        super().__init__(binary_path, config_path)

    @staticmethod
    def get_duplicate(*args, **kwargs) -> dict | None:
        """Mock get_duplicate method."""
        _ = args
        _ = kwargs
        return {"case_id": "case_id"}

    @staticmethod
    def delete_case(*args, **kwargs) -> None:
        """Mock delete_case method."""
        _ = args
        _ = kwargs
        return None


@pytest.fixture(name="mock_loqusdb_api")
def mock_loqusdb_api(filled_file) -> MockLoqusdbAPI:
    """Mock Loqusdb API."""
    return MockLoqusdbAPI(binary_path=filled_file, config_path=filled_file)
