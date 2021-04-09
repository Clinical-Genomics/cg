"""Fixtures for cli tests"""
from functools import partial

import pytest
from cg.cli import base
from cg.store import Store
from click.testing import CliRunner


@pytest.fixture(name="cli_runner")
def fixture_cli_runner() -> CliRunner:
    """Create a CliRunner"""
    return CliRunner()


@pytest.fixture(name="application_tag")
def fixture_application_tag() -> str:
    """Create a CliRunner"""
    return "dummy_tag"


@pytest.fixture
def invoke_cli(cli_runner):
    """Create a CLiRunner with our CLI preloaded"""
    return partial(cli_runner.invoke, base)


@pytest.fixture(name="base_context")
def fixture_base_context(base_store: Store) -> dict:
    """context to use in cli"""
    return {"trailblazer_api": None, "status_db": base_store}


@pytest.fixture(name="disk_store")
def fixture_disk_store(base_context: dict) -> Store:
    """context to use in cli"""
    return base_context["status_db"]
