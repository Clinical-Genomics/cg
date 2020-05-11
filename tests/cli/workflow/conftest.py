"""Fixtures for cli analysis tests"""
from datetime import datetime

import pytest

from cg.store import Store, models


@pytest.fixture
def base_context(analysis_store) -> dict:
    """context to use in cli"""
    return {"db": analysis_store}


@pytest.fixture(scope="function", name="analysis_store")
def fixture_analysis_store(base_store: Store, helpers) -> Store:
    """ store to be used in tests"""
    _store = base_store

    case = helpers.add_family(_store, "dna_case")
    sample = helpers.add_sample(_store, "dna_sample", is_rna=False)
    helpers.add_relationship(_store, sample=sample, family=case)

    case = helpers.add_family(_store, "rna_case")
    sample = helpers.add_sample(_store, "rna_sample", is_rna=True)
    helpers.add_relationship(_store, sample=sample, family=case)

    return _store


@pytest.fixture(scope="function")
def dna_case(analysis_store, helpers) -> models.Family:
    """case with dna application"""
    cust = helpers.ensure_customer(analysis_store)
    return analysis_store.find_family(cust, "dna_case")


@pytest.fixture(scope="function")
def rna_case(analysis_store, helpers) -> models.Family:
    """case with rna application"""
    cust = helpers.ensure_customer(analysis_store)
    return analysis_store.find_family(cust, "rna_case")


def ensure_application_version(store, is_rna=False):
    """utility function to return existing or create application version for tests"""

    if is_rna:
        application_tag = "rna_tag"
        category = "wts"
    else:
        application_tag = "dna_tag"
        category = "wgs"

    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(
            tag=application_tag,
            category=category,
            description="dummy_description",
            percent_kth=80,
        )
        store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = store.application_version(application, 1)
    if not version:
        version = store.add_version(
            application, 1, valid_from=datetime.now(), prices=prices
        )

        store.add_commit(version)
    return version


def add_sample(store, sample_id="sample_test", gender="female", is_rna=False):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)

    application_version_id = ensure_application_version(store, is_rna).id

    sample = store.add_sample(name=sample_id, sex=gender, sequenced_at=datetime.now())
    sample.application_version_id = application_version_id
    sample.customer = customer
    store.add_commit(sample)
    return sample


def add_case(store, case_name="case_test", customer_id="cust_test"):
    """utility function to add a case to use in tests"""
    panel = ensure_panel(store)
    customer = ensure_customer(store, customer_id)
    family = store.add_family(name=case_name, panels=panel.name)
    family.customer = customer
    store.add_commit(family)
    return family
