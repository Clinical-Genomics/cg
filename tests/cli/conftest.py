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


@pytest.fixture(name="analysis_family")
def fixture_analysis_family():
    """Build an example family."""
    family = {
        "name": "family",
        "internal_id": "yellowhog",
        "panels": ["IEM", "EP"],
        "samples": [
            {
                "name": "son",
                "sex": "male",
                "internal_id": "ADM1",
                "data_analysis": "mip",
                "father": "ADM2",
                "mother": "ADM3",
                "status": "affected",
                "ticket_number": 123456,
                "reads": 5000000,
            },
            {
                "name": "father",
                "sex": "male",
                "internal_id": "ADM2",
                "data_analysis": "mip",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 6000000,
            },
            {
                "name": "mother",
                "sex": "female",
                "internal_id": "ADM3",
                "data_analysis": "mip",
                "status": "unaffected",
                "ticket_number": 123456,
                "reads": 7000000,
            },
        ],
    }
    return family


@pytest.yield_fixture(scope="function")
def analysis_store(base_store, analysis_family):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer("cust000")
    family = base_store.Family(
        name=analysis_family["name"],
        panels=analysis_family["panels"],
        internal_id=analysis_family["internal_id"],
        priority="standard",
    )
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application("WGTPCFC030").versions[0]
    for sample_data in analysis_family["samples"]:
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=sample_data["sex"],
            internal_id=sample_data["internal_id"],
            ticket=sample_data["ticket_number"],
            reads=sample_data["reads"],
            data_analysis=sample_data["data_analysis"],
        )
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family["samples"]:
        sample_obj = base_store.sample(sample_data["internal_id"])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data["status"],
            father=base_store.sample(sample_data["father"])
            if sample_data.get("father")
            else None,
            mother=base_store.sample(sample_data["mother"])
            if sample_data.get("mother")
            else None,
        )
        base_store.add(link)
    base_store.commit()
    yield base_store


@pytest.yield_fixture(scope="function")
def analysis_store_wes(base_store, analysis_family):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer("cust000")
    family = base_store.Family(
        name=analysis_family["name"],
        panels=analysis_family["panels"],
        internal_id=analysis_family["internal_id"],
        priority="standard",
    )
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application("EXXCUSR000").versions[0]
    for sample_data in analysis_family["samples"]:
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=sample_data["sex"],
            internal_id=sample_data["internal_id"],
            ticket=sample_data["ticket_number"],
            reads=sample_data["reads"],
            data_analysis=sample_data["data_analysis"],
        )
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family["samples"]:
        sample_obj = base_store.sample(sample_data["internal_id"])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data["status"],
            father=base_store.sample(sample_data["father"])
            if sample_data.get("father")
            else None,
            mother=base_store.sample(sample_data["mother"])
            if sample_data.get("mother")
            else None,
        )
        base_store.add(link)
    base_store.commit()
    yield base_store


@pytest.fixture
def base_context(base_store: Store) -> dict:
    """context to use in cli"""
    return {"tb": None, "db": base_store}
