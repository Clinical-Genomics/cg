"""Fixtures for cli tests"""

import pytest
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner


@pytest.fixture(name="cli_runner")
def fixture_cli_runner() -> CliRunner:
    """Create a CliRunner"""
    return CliRunner()


@pytest.fixture(name="application_tag")
def fixture_application_tag() -> str:
    """Return a dummy tag"""
    return "dummy_tag"


@pytest.fixture(name="base_context")
def fixture_base_context(
    base_store: Store, housekeeper_api: HousekeeperAPI, cg_config_object: CGConfig
) -> CGConfig:
    """context to use in cli"""
    cg_config_object.status_db_ = base_store
    cg_config_object.housekeeper_api_ = housekeeper_api
    return cg_config_object


@pytest.fixture(name="before_date")
def fixture_before_date() -> str:
    """Return a before date string"""
    return "1999-12-31"


@pytest.fixture(name="disk_store")
def fixture_disk_store(base_context: CGConfig) -> Store:
    """context to use in cli"""
    return base_context.status_db
