"""Tests the findbusinessdata part of the cg.store.api"""
from datetime import datetime


def test_find_analysis_via_date(sample_store):
    # GIVEN a case with an analysis with a startdate in the database
    analysis = add_analysis(store=sample_store, started_at=datetime.now())
    assert analysis.started_at

    # WHEN getting analysis via case_id and start date
    db_analysis = sample_store.analysis(analysis.family, analysis.started_at)

    # THEN the analysis should have been retrieved
    assert db_analysis == analysis


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


def ensure_panel(store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(store, customer_id)
    panel = store.panel(panel_id)
    if not panel:
        panel = store.add_panel(
            customer=customer,
            name=panel_id,
            abbrev=panel_id,
            version=1.0,
            date=datetime.now(),
            genes=1,
        )
        store.add_commit(panel)
    return panel


def add_family(store, family_id="family_test", customer_id="cust_test"):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(store)
    customer = ensure_customer(store, customer_id)
    family = store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    store.add_commit(family)
    return family


def add_analysis(store, family=None, started_at=None):
    """Utility function to add an analysis for tests"""

    if not family:
        family = add_family(store)

    analysis = store.add_analysis(pipeline="", version="")

    if started_at:
        analysis.started_at = started_at

    analysis.family = family
    store.add_commit(analysis)
    return analysis


def ensure_application_version(disk_store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag, category="wgs", description="dummy_description", percent_kth=80
        )
        disk_store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

        disk_store.add_commit(version)
    return version


def add_sample(store, sample_name="sample_test", uploaded_to_loqus=None):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex="unknown")
    sample.application_version_id = application_version_id
    sample.customer = customer
    if uploaded_to_loqus:
        sample.loqusdb_id = uploaded_to_loqus
    store.add_commit(sample)
    return sample
