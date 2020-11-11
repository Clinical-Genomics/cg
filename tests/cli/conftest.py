"""Fixtures for cli tests"""
from functools import partial

import pytest
from click.testing import CliRunner

from cg.cli import base
from cg.store import Store


@pytest.fixture(name="cli_runner")
def fixture_cli_runner():
    """Create a CliRunner"""
    runner = CliRunner()
    return runner


@pytest.fixture
def invoke_cli(cli_runner):
    """Create a CLiRunner with our CLI preloaded"""
    return partial(cli_runner.invoke, base)


@pytest.fixture
def base_context(base_store: Store) -> dict:
    """context to use in cli"""
    return {"trailblazer_api": None, "status_db": base_store}
