from pathlib import Path
from unittest.mock import patch

import pytest

from cg.meta.archive.ddn import DDNApi
from cg.models.cg_config import DDNConfig


@pytest.fixture(name="ddn_config")
def fixture_ddn_config() -> DDNConfig:
    """Returns a dummy DDNConfig."""
    return DDNConfig(
        database_name="test_db",
        user="test_user",
        password="DummyPassword",
        url="some/api/url.com",
        local_storage="local@storage:",
        archive_repository="archive@repisitory:",
    )


@pytest.fixture(name="ddn_api")
def fixture_ddn_api(ddn_config) -> DDNApi:
    """Returns a DDNApi without tokens being set."""
    with patch.object(DDNApi, "__init__", lambda x, y: None):
        ddn_api: DDNApi = DDNApi(ddn_config)
        for key, value in ddn_config.dict().items():
            setattr(ddn_api, key, value)
        return ddn_api


@pytest.fixture(name="remote_directory")
def fixture_remote_directory() -> Path:
    """Returns a dummy path."""
    return Path("/some/place")


@pytest.fixture(name="local_directory")
def fixture_local_directory() -> Path:
    """Returns a dummy path with /home as its root."""
    return Path("/home/other/place")
