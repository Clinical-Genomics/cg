"""Fixtures for cli analysis tests"""
from datetime import datetime

import pytest

from cg.store import Store, models


@pytest.fixture
def base_context(analysis_store) -> dict:
    """context to use in cli"""
    return {"db": analysis_store}


@pytest.fixture(scope="function", name="analysis_store")
def fixture_analysis_store(base_store: Store) -> Store:
    """ store to be used in tests"""
    _store = base_store

    case = add_case(_store, "dna_case")
    sample = add_sample(_store, "dna_sample", is_rna=False)
    _store.relate_sample(case, sample, status="unknown")
    _store.commit()

    case = add_case(_store, "rna_case")
    sample = add_sample(_store, "rna_sample", is_rna=True)
    _store.relate_sample(case, sample, status="unknown")
    _store.commit()

    return _store


@pytest.fixture(scope="function")
def dna_case(analysis_store) -> models.Family:
    """case with dna application"""
    cust = ensure_customer(analysis_store)
    return analysis_store.find_family(cust, "dna_case")


@pytest.fixture(scope="function")
def rna_case(analysis_store) -> models.Family:
    """case with rna application"""
    cust = ensure_customer(analysis_store)
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
            tag=application_tag, category=category, description="dummy_description"
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


def ensure_customer(store, customer_id="cust_test"):
    """utility function to return existing or create customer for tests"""
    customer_group = store.customer_group("dummy_group")
    if not customer_group:
        customer_group = store.add_customer_group("dummy_group", "dummy group")

        customer = store.add_customer(
            internal_id=customer_id,
            name="Test Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        store.add_commit(customer)
    customer = store.customer(customer_id)
    return customer


def add_sample(store, sample_id="sample_test", gender="female", is_rna=False):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)

    application_version_id = ensure_application_version(store, is_rna).id

    sample = store.add_sample(name=sample_id, sex=gender, sequenced_at=datetime.now())
    sample.application_version_id = application_version_id
    sample.customer = customer
    store.add_commit(sample)
    return sample


def ensure_panel(disk_store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.panel(panel_id)
    if not panel:
        panel = disk_store.add_panel(
            customer=customer,
            name=panel_id,
            abbrev=panel_id,
            version=1.0,
            date=datetime.now(),
            genes=1,
        )
        disk_store.add_commit(panel)
    return panel


def add_case(store, case_name="case_test", customer_id="cust_test"):
    """utility function to add a case to use in tests"""
    panel = ensure_panel(store)
    customer = ensure_customer(store, customer_id)
    family = store.add_family(name=case_name, panels=panel.name)
    family.customer = customer
    store.add_commit(family)
    return family
