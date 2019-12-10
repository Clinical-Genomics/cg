"""This script tests the cli methods to add families to status-db"""
from datetime import datetime

from cg.cli.status import cases
from cg.store import Store


def test_lists_sample_in_unreceived_samples(
    cli_runner, base_context, base_store: Store
):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    family = add_family(base_store)
    sample1 = add_sample(base_store, "sample1")
    base_store.relate_sample(family, sample1, status="unknown")
    base_store.commit()

    # WHEN listing cases
    result = cli_runner.invoke(cases, ["-o", "count"], obj=base_context)

    # THEN the family should be listed
    assert result.exit_code == 0
    assert family.internal_id in result.output
    assert "0/1" in result.output


def test_lists_samples_in_unreceived_samples(
    cli_runner, base_context, base_store: Store
):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    family = add_family(base_store)
    sample1 = add_sample(base_store, "sample1")
    sample2 = add_sample(base_store, "sample2")
    base_store.relate_sample(family, sample1, status="unknown")
    base_store.relate_sample(family, sample2, status="unknown")
    base_store.commit()

    # WHEN listing cases
    result = cli_runner.invoke(cases, ["-o", "count"], obj=base_context)

    # THEN the family should be listed
    assert result.exit_code == 0
    assert family.internal_id in result.output
    assert "0/2" in result.output


def test_lists_family(cli_runner, base_context, base_store: Store):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    family = add_family(base_store)

    # WHEN listing cases
    result = cli_runner.invoke(cases, obj=base_context)

    # THEN the family should be listed
    assert result.exit_code == 0
    assert family.internal_id in result.output


def ensure_application_version(store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(
            tag=application_tag, category="wgs", description="dummy_description"
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


def add_sample(store, sample_id="sample_test", gender="female"):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_id, sex=gender)
    sample.application_version_id = application_version_id
    sample.customer = customer
    store.add_commit(sample)
    return sample


def add_panel(store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(store, customer_id)
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
    panel = add_panel(store)
    customer = ensure_customer(store, customer_id)
    family = store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    store.add_commit(family)
    return family
