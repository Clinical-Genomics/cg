"""Fixtures for cli analysis tests"""

import pytest

from cg.store import Store, models


@pytest.fixture
def base_context(analysis_store) -> dict:
    """context to use in cli"""
    return {"db": analysis_store}


@pytest.fixture(name="workflow_case_id")
def fixture_workflow_case_id() -> dict:
    """Return a special case id"""
    return "dna_case"


@pytest.fixture(scope="function", name="analysis_store")
def fixture_analysis_store(base_store: Store, workflow_case_id, helpers) -> Store:
    """Store to be used in tests"""
    _store = base_store

    case = helpers.add_family(_store, workflow_case_id)

    sample = helpers.add_sample(_store, "dna_sample", is_rna=False)
    helpers.add_relationship(_store, sample=sample, family=case)

    case = helpers.add_family(_store, "rna_case")
    sample = helpers.add_sample(_store, "rna_sample", is_rna=True)
    helpers.add_relationship(_store, sample=sample, family=case)

    return _store


@pytest.fixture(scope="function")
def dna_case(analysis_store, helpers) -> models.Family:
    """Case with DNA application"""
    cust = helpers.ensure_customer(analysis_store)
    return analysis_store.find_family(cust, "dna_case")


@pytest.fixture(scope="function")
def rna_case(analysis_store, helpers) -> models.Family:
    """Case with RNA application"""
    cust = helpers.ensure_customer(analysis_store)
    return analysis_store.find_family(cust, "rna_case")
