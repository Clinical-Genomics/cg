import pytest


@pytest.fixture(name="config")
def fixture_config(root_path) -> dict:
    """Return a dictionary with housekeeper api configs for testing"""
    config = {
        "gisaid": {"binary_path": "/path/to/gisaid", "submitter": "some submitter"},
        "housekeeper": {"database": "sqlite:///:memory:", "root": str(root_path)},
    }
    return config
