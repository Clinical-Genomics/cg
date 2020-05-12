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


@pytest.yield_fixture(scope="function")
def analysis_store(base_store, analysis_family, wgs_application_tag, helpers):
    """Setup a store instance for testing analysis API."""
    family_obj = helpers.add_family(base_store)

    for sample_data in analysis_family["samples"]:
        sample_obj = helpers.add_sample(
            base_store,
            gender=sample_data["sex"],
            sample_id=sample_data["internal_id"],
            application_tag=wgs_application_tag,
            reads=sample_data["reads"],
            data_analysis=sample_data["data_analysis"],
            ticket=sample_data["ticket_number"],
        )
        helpers.add_relationship(
            base_store,
            family=family_obj,
            sample=sample_obj,
            status=sample_data["status"],
        )

    yield base_store


@pytest.fixture
def base_context(base_store: Store) -> dict:
    """context to use in cli"""
    return {"tb": None, "db": base_store}
