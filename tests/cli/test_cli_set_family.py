"""This script tests the cli methods to set families to status-db"""
from datetime import datetime

from cg.store import Store


def test_set_family_without_options(invoke_cli, disk_store: Store):
    """Test to set a family using only the required arguments"""
    # GIVEN a database with a family
    family_id = add_family(disk_store).internal_id
    assert disk_store.Family.query.count() == 1

    # WHEN setting a family
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'set', 'family', family_id])

    # THEN then it should abort
    assert result.exit_code == 1


def test_set_family_bad_family(invoke_cli, disk_store: Store):
    """Test to set a family using a non-existing family """
    # GIVEN an empty database

    # WHEN setting a family
    db_uri = disk_store.uri
    name = 'dummy_name'
    result = invoke_cli(['--database', db_uri, 'set', 'family', name])

    # THEN then it should complain in missing family instead of setting a family
    assert result.exit_code == 1


def test_set_family_bad_panel(invoke_cli, disk_store: Store):
    """Test to set a family using a non-existing panel"""
    # GIVEN a database with a family

    # WHEN setting a family
    db_uri = disk_store.uri
    panel_id = 'dummy_panel'
    name = add_family(disk_store)
    result = invoke_cli(['--database', db_uri, 'set', 'family', '--panel',
                         panel_id, name])

    # THEN then it should complain in missing panel instead of setting a family
    assert result.exit_code == 1
    assert panel_id not in disk_store.Family.query.first().panels


def test_set_family_panel(invoke_cli, disk_store: Store):
    """Test to set a family using a non-existing panel"""
    # GIVEN a database with a family and another non set panel
    panel_id = add_panel(disk_store, 'a_panel')
    name = add_family(disk_store)
    assert panel_id not in disk_store.Family.query.first().panels

    # WHEN setting a family
    db_uri = disk_store.uri
    result = invoke_cli(['--database', db_uri, 'set', 'family', '--panel',
                         panel_id, name])

    # THEN then it should set panel on the family
    assert result.exit_code == 0
    assert panel_id in disk_store.Family.query.first().panels


def test_set_family_priority(invoke_cli, disk_store: Store):
    """Test that the added family get the priority we send in"""
    # GIVEN a database with a family
    name = add_family(disk_store)
    priority = 'priority'
    assert disk_store.Family.query.first().priority_human != priority

    # WHEN setting a family
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'set', 'family',
         '--priority', priority, name])

    # THEN then it should have been set
    assert result.exit_code == 0
    assert disk_store.Family.query.count() == 1
    assert disk_store.Family.query.first().priority_human == priority


def add_panel(disk_store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to set a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                 version=1.0,
                                 date=datetime.now(), genes=1)
    disk_store.add_commit(panel)
    return panel_id


def add_application(disk_store, application_tag='dummy_tag'):
    """utility function to set an application to use in tests"""
    application = disk_store.add_application(tag=application_tag, category='wgs',
                                             description='dummy_description')
    disk_store.add_commit(application)
    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = disk_store.add_version(application, 1, valid_from=datetime.now(),
                                     prices=prices)

    disk_store.add_commit(version)
    return application_tag


def ensure_application_version(disk_store, application_tag='dummy_tag'):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(tag=application_tag, category='wgs',
                                                 description='dummy_description')
        disk_store.add_commit(application)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(),
                                         prices=prices)

        disk_store.add_commit(version)
    return version.id


def ensure_customer(disk_store, customer_id='cust_test'):
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group('dummy_group')
    if not customer_group:
        customer_group = disk_store.add_customer_group('dummy_group', 'dummy group')

        customer = disk_store.add_customer(internal_id=customer_id, name="Test Customer",
                                           scout_access=False, customer_group=customer_group,
                                           invoice_address='dummy_address',
                                           invoice_reference='dummy_reference')
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def add_family(disk_store, family_id='family_test', customer_id='cust_test'):
    """utility function to set a family to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = add_panel(disk_store)
    family = disk_store.add_family(name=family_id, panels=panel)
    family.customer = customer
    disk_store.add_commit(family)
    return family.internal_id
