"""This script tests the cli methods to set families to status-db"""
from datetime import datetime

from cg.cli.set import family
from cg.store import Store

SUCCESS = 0


def test_set_family_without_options(cli_runner, base_context, base_store: Store):
    """Test to set a family using only the required arguments"""
    # GIVEN a database with a family
    family_id = add_family(base_store).internal_id
    assert base_store.Family.query.count() == 1

    # WHEN setting a family
    result = cli_runner.invoke(family, [family_id], obj=base_context)

    # THEN then it should abort
    assert result.exit_code != SUCCESS


def test_set_family_bad_family(cli_runner, base_context):
    """Test to set a family using a non-existing family """
    # GIVEN an empty database

    # WHEN setting a family
    family_id = "dummy_name"
    result = cli_runner.invoke(family, [family_id], obj=base_context)

    # THEN then it should complain on missing family
    assert result.exit_code != SUCCESS


def test_set_family_bad_panel(cli_runner, base_context, base_store: Store):
    """Test to set a family using a non-existing panel"""
    # GIVEN a database with a family

    # WHEN setting a family
    panel_id = "dummy_panel"
    family_id = add_family(base_store).internal_id
    result = cli_runner.invoke(
        family, [family_id, "--panel", panel_id], obj=base_context
    )

    # THEN then it should complain in missing panel instead of setting a value
    assert result.exit_code != SUCCESS
    assert panel_id not in base_store.Family.query.first().panels


def test_set_family_panel(cli_runner, base_context, base_store: Store):
    """Test to set a family using an existing panel"""
    # GIVEN a database with a family and a panel not yet added to the family
    panel_id = add_panel(base_store, "a_panel").name
    family_id = add_family(base_store).internal_id
    assert panel_id not in base_store.Family.query.first().panels

    # WHEN setting a panel of a family
    result = cli_runner.invoke(
        family, [family_id, "--panel", panel_id], obj=base_context
    )

    # THEN then it should set panel on the family
    assert result.exit_code == SUCCESS
    assert panel_id in base_store.Family.query.first().panels


def test_set_family_priority(cli_runner, base_context, base_store: Store):
    """Test that the added family gets the priority we send in"""
    # GIVEN a database with a family
    family_id = add_family(base_store).internal_id
    priority = "priority"
    assert base_store.Family.query.first().priority_human != priority

    # WHEN setting a family

    result = cli_runner.invoke(
        family, [family_id, "--priority", priority], obj=base_context
    )

    # THEN then it should have been set
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1
    assert base_store.Family.query.first().priority_human == priority


def add_panel(store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to set a panel to use in tests"""
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


def add_application(store, application_tag="dummy_tag"):
    """utility function to set an application to use in tests"""
    application = store.add_application(
        tag=application_tag,
        category="wgs",
        description="dummy_description",
        percent_kth=80,
    )
    store.add_commit(application)
    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = store.add_version(
        application, 1, valid_from=datetime.now(), prices=prices
    )

    store.add_commit(version)
    return application


def ensure_application_version(store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(
            tag=application_tag,
            category="wgs",
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


def add_family(store, family_id="family_test", customer_id="cust_test"):
    """utility function to set a family to use in tests"""
    customer = ensure_customer(store, customer_id)
    panel_id = add_panel(store).name
    family_obj = store.add_family(name=family_id, panels=panel_id)
    family_obj.customer = customer
    store.add_commit(family_obj)
    return family_obj
