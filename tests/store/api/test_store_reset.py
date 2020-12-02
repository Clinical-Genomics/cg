"""Tests for reset part of the store API"""
from cg.constants import Pipeline

"""Tests for reset part of the store API"""

from datetime import datetime, timedelta

from cg.store import Store


def test_reset_observation(store: Store):
    # GIVEN a store with a case with loqus-links
    family = add_family(store)
    sample = add_sample(store, loqusdb_links=True)
    store.relate_sample(family=family, sample=sample, status="unknown")
    assert sample.loqusdb_id is not None

    # WHEN calling reset observations
    store.reset_observations(case_id=family.internal_id)

    # THEN the links to observations in loqusdb should have been reset
    assert sample.loqusdb_id is None


def ensure_application_version(disk_store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag,
            category="wgs",
            description="dummy_description",
            percent_kth=80,
            percent_reads_guaranteed=75,
        )
        disk_store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

        disk_store.add_commit(version)
    return version


def ensure_customer(disk_store, customer_id="cust_test"):
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group("dummy_group")
    if not customer_group:
        customer_group = disk_store.add_customer_group("dummy_group", "dummy group")

        customer = disk_store.add_customer(
            internal_id=customer_id,
            name="Test Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def add_sample(store, sample_name="sample_test", loqusdb_links=False):
    """utility function to add a sample to use in tests"""

    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex="unknown")
    sample.application_version_id = application_version_id
    sample.customer = customer
    if loqusdb_links:
        sample.loqusdb_id = True
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


def add_family(
    disk_store,
    family_id="family_test",
    customer_id="cust_test",
    ordered_days_ago=0,
    action=None,
    priority=None,
    data_analysis=Pipeline.MIP_DNA,
):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(data_analysis=data_analysis, name=family_id, panels=panel.name)
    family.customer = customer
    family.ordered_at = datetime.now() - timedelta(days=ordered_days_ago)
    if action:
        family.action = action
    if priority:
        family.priority = priority
    disk_store.add_commit(family)
    return family
